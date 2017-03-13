"""
Code adapted from here: http://code.activestate.com/recipes/114642-pinhole/, licensed under Python Software Foundation License

usage 'pinhole port host [newport]'

Pinhole forwards the port to the host specified.
The optional newport parameter may be used to
redirect to a different port.

eg. pinhole 80 webserver
    Forward all incoming WWW sessions to webserver.

    pinhole 23 localhost 2323
    Forward all telnet sessions to port 2323 on localhost.
"""

import uuid
from socket import *
from threading import Thread
import time

import collections

import http_parser
from parser_utils import intialize_parser, parse

LOGGING = 0


def log(s):
    if LOGGING:
        print('%s:%s' % (time.ctime(), s))
        sys.stdout.flush()


class RequestResponse:
    def __init__(self, request=None, response=None):
        self.guid = uuid.uuid4()
        self.response = response
        self.request = request

    def __str__(self):
        s = "====================================================\n"
        s += "Communication " + str(self.guid) + "\n"
        s += "REQUEST:\n"
        s += str(self.request) + "\n"
        s += "RESPONSE:\n"
        s += str(self.response) + "\n"
        s += "====================================================\n"
        return s


class Communication:
    def __init__(self):
        self.pending_requests = collections.deque()
        self.pending_responses = collections.deque()

    def add_message(self, message, tag):
        if tag == "request":
            self.add_request(message)
        elif tag == "response":
            self.add_response(message)
        else:
            raise Exception("Unknown tag " + tag)

    def add_request(self, request):
        if self.pending_responses:
            request_response = self.pending_responses.popleft()
            request_response.request = request
            self.have_request_response(request_response)
        else:
            request_response = RequestResponse(request=request)
            self.pending_requests.append(request_response)
            self.have_request_response(request_response)

    def add_response(self, response):
        if self.pending_requests:
            request_response = self.pending_requests.popleft()
            request_response.response = response
            self.have_request_response(request_response)
        else:
            request_response = RequestResponse(response=response)
            self.pending_responses.append(request_response)
            self.have_request_response(request_response)

    def have_request_response(self, request_response):
        print(request_response)


class PipeThread(Thread):
    pipes = []

    def __init__(self, source, sink, tag, communication, newhost, newport):
        Thread.__init__(self)
        self.communication = communication
        self.tag = tag
        self.source = source
        self.sink = sink

        if newport != 80:
            self.host_header = b"%s:%s" % (str(newhost).encode(), str(newport).encode())
        else:
            self.host_header = b"%s" % (str(newhost).encode())

        log('Creating new pipe thread  %s ( %s -> %s )' % \
            (self, source.getpeername(), sink.getpeername()))
        PipeThread.pipes.append(self)
        log('%s pipes active' % len(PipeThread.pipes))

    def send(self, data):
        # print(data)
        self.sink.send(data)

    def send_request(self, msg):
        for data in msg.to_bytes():
            self.send(data)

    def run(self):
        parser = intialize_parser(http_parser.get_http_request)
        while 1:
            try:
                try:
                    data = self.source.recv(1024)
                except ConnectionResetError:
                    data = None

                if self.tag == "request":
                    for msg in parse(parser, data):
                        self.communication.add_message(msg, self.tag)
                        # print(msg)
                        if msg.headers.get(b"Host"):
                            msg.headers[b"Host"] = self.host_header
                        self.send_request(msg)
                else:
                    for msg in parse(parser, data):
                        self.communication.add_message(msg, self.tag)
                        # print(msg)
                        if msg.headers.get(b"Transfer-Encoding", "") == b"chunked":
                            del msg.headers[b"Transfer-Encoding"]
                            msg.headers[b"Content-Length"] = str(len(msg.body)).encode()
                        self.send_request(msg)

                if not data:
                    break
            except Exception as ex:
                print(ex)
                break

        log('%s terminating' % self)
        PipeThread.pipes.remove(self)
        log('%s pipes active' % len(PipeThread.pipes))

        self.sink.shutdown(socket.SHUT_WR)


class Pinhole(Thread):
    def __init__(self, port, newhost, newport, communication_class=Communication):
        Thread.__init__(self)
        log('Redirecting: localhost:%s -> %s:%s' % (port, newhost, newport))
        self.newhost = newhost
        self.newport = newport
        self.communication_class = communication_class

    def run(self):
        try:
            self.sock = socket(AF_INET, SOCK_STREAM)
            self.sock.bind(('', port))
            self.sock.listen(5)
            while 1:
                newsock, address = self.sock.accept()
                log('Creating new session for %s' % address)
                fwd = socket(AF_INET, SOCK_STREAM)
                fwd.connect((self.newhost, self.newport))
                comm = self.communication_class()
                PipeThread(newsock, fwd, 'request', comm, newhost, newport).start()
                PipeThread(fwd, newsock, 'response', comm, newhost, newport).start()
        finally:
            self.sock.close()


if __name__ == '__main__':
    print('Starting Pinhole')

    import sys

    # sys.stdout = open('pinhole.log', 'w')

    if len(sys.argv) > 1:
        port = newport = int(sys.argv[1])
        newhost = sys.argv[2]
        if len(sys.argv) == 4: newport = int(sys.argv[3])
        Pinhole(port, newhost, newport).start()
    else:
        Pinhole(8003, 'www.example.com', 80).start()
