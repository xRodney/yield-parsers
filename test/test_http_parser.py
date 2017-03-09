import http_parser
from parser_utils import parse, intialize_parser


def chunks(l, n):
    """Yield successive n-sized chunks from l."""
    for i in range(0, len(l), n):
        yield l[i:i + n]


def test_two_requests_whole():
    msg = b"GET / HTTP/1.1\r\nHost: www.example.com\r\n\r\nGET / HTTP/1.1\r\nHost: www.example.com\r\n\r\n"

    parser = intialize_parser(http_parser.get_http_request)
    parsed_messages = parse(parser, msg)

    assert len(parsed_messages) == 2
    for parsed_message in parsed_messages:
        assert parsed_message.headers['Host'] == "www.example.com"
        assert parsed_message.body == None
        assert parsed_message.method == "GET"
        assert parsed_message.path == "/"


def test_two_requests_in_pieces():
    msg = b"GET / HTTP/1.1\r\nHost: www.example.com\r\n\r\nGET / HTTP/1.1\r\nHost: www.example.com\r\n\r\n"
    msgs = chunks(msg, 15)

    parser = intialize_parser(http_parser.get_http_request)
    parsed_messages = []

    for data in msgs:
        parsed_messages += parse(parser, data)

    assert len(parsed_messages) == 2
    for parsed_message in parsed_messages:
        assert parsed_message.headers['Host'] == "www.example.com"
        assert parsed_message.body == None
        assert parsed_message.method == "GET"
        assert parsed_message.path == "/"


def test_two_responses_whole():
    msg = b"HTTP/1.1 200 OK\r\n" + \
          b"Content-Type: text/plain; charset=utf-8\r\n" + \
          b"Content-Length: 6\r\n" + \
          b"\r\n" + \
          b"abcd\r\n"

    msg = msg * 2
    parser = intialize_parser(http_parser.get_http_request)
    parsed_messages = parse(parser, msg)

    assert len(parsed_messages) == 2
    for parsed_message in parsed_messages:
        assert parsed_message.headers['Content-Type'] == "text/plain; charset=utf-8"
        assert parsed_message.body == b"abcd\r\n"


def test_one_response_no_length():
    msg = b"HTTP/1.1 200 OK\r\n" + \
          b"Content-Type: text/plain; charset=utf-8\r\n" + \
          b"\r\n" + \
          b"abcd\r\n"

    parser = intialize_parser(http_parser.get_http_request)
    parsed_messages = parse(parser, msg)

    assert len(parsed_messages) == 1
    for parsed_message in parsed_messages:
        assert parsed_message.headers['Content-Type'] == "text/plain; charset=utf-8"
        assert parsed_message.body == b"abcd\r\n"


def test_two_responses_in_pieces():
    msg = b"HTTP/1.1 200 OK\r\n" + \
          b"Content-Type: text/plain; charset=utf-8\r\n" + \
          b"Content-Length: 6\r\n" + \
          b"\r\n" + \
          b"abcd\r\n"

    msg = msg * 3
    parser = intialize_parser(http_parser.get_http_request)
    msgs = chunks(msg, 15)
    parsed_messages = []

    for data in msgs:
        parsed_messages += parse(parser, data)

    assert len(parsed_messages) == 3
    for parsed_message in parsed_messages:
        assert parsed_message.headers['Content-Type'] == "text/plain; charset=utf-8"
        assert parsed_message.body == b"abcd\r\n"


def test_one_response_chunked_whole():
    msg = b"HTTP/1.1 200 OK\r\n" + \
          b"Content-Type: text/plain; charset=utf-8\r\n" + \
          b"Transfer-Encoding: chunked\r\n" + \
          b"\r\n" + \
          b"4\r\n" + \
          b"Wiki\r\n" + \
          b"5\r\n" + \
          b"pedia\r\n" + \
          b"E\r\n" + \
          b" in\r\n" + \
          b"\r\n" + \
          b"chunks.\r\n" + \
          b"0\r\n" + \
          b"\r\n"

    parser = intialize_parser(http_parser.get_http_request)
    parsed_messages = parse(parser, msg)
    assert len(parsed_messages) == 1
    for parsed_message in parsed_messages:
        assert parsed_message.headers['Content-Type'] == "text/plain; charset=utf-8"
        assert parsed_message.body == b"Wikipedia in\r\n\r\nchunks."


def test_one_response_chunked_in_parts():
    msg = b"HTTP/1.1 200 OK\r\n" + \
          b"Content-Type: text/plain; charset=utf-8\r\n" + \
          b"Transfer-Encoding: chunked\r\n" + \
          b"\r\n" + \
          b"4\r\n" + \
          b"Wiki\r\n" + \
          b"5\r\n" + \
          b"pedia\r\n" + \
          b"E\r\n" + \
          b" in\r\n" + \
          b"\r\n" + \
          b"chunks.\r\n" + \
          b"0\r\n" + \
          b"\r\n"

    parser = intialize_parser(http_parser.get_http_request)
    msgs = chunks(msg, 15)
    parsed_messages = []

    for data in msgs:
        parsed_messages += parse(parser, data)

    assert len(parsed_messages) == 1
    for parsed_message in parsed_messages:
        assert parsed_message.headers['Content-Type'] == "text/plain; charset=utf-8"
        assert parsed_message.body == b"Wikipedia in\r\n\r\nchunks."


def test_two_responses_chunked():
    msg = b"HTTP/1.1 200 OK\r\n" + \
          b"Content-Type: text/plain; charset=utf-8\r\n" + \
          b"Transfer-Encoding: chunked\r\n" + \
          b"\r\n" + \
          b"4\r\n" + \
          b"Wiki\r\n" + \
          b"5\r\n" + \
          b"pedia\r\n" + \
          b"E\r\n" + \
          b" in\r\n" + \
          b"\r\n" + \
          b"chunks.\r\n" + \
          b"0\r\n" + \
          b"\r\n"

    msg = msg * 2
    parser = intialize_parser(http_parser.get_http_request)
    parsed_messages = parse(parser, msg)

    assert len(parsed_messages) == 2
    for parsed_message in parsed_messages:
        assert parsed_message.headers['Content-Type'] == "text/plain; charset=utf-8"
        assert parsed_message.body == b"Wikipedia in\r\n\r\nchunks."


def test_two_responses_chunked_in_parts():
    msg = b"HTTP/1.1 200 OK\r\n" + \
          b"Content-Type: text/plain; charset=utf-8\r\n" + \
          b"Transfer-Encoding: chunked\r\n" + \
          b"\r\n" + \
          b"4\r\n" + \
          b"Wiki\r\n" + \
          b"5\r\n" + \
          b"pedia\r\n" + \
          b"E\r\n" + \
          b" in\r\n" + \
          b"\r\n" + \
          b"chunks.\r\n" + \
          b"0\r\n" + \
          b"\r\n"

    msg = msg * 2
    parser = intialize_parser(http_parser.get_http_request)

    msgs = chunks(msg, 15)
    parsed_messages = []

    for data in msgs:
        parsed_messages += parse(parser, data)

    assert len(parsed_messages) == 2
    for parsed_message in parsed_messages:
        assert parsed_message.headers['Content-Type'] == "text/plain; charset=utf-8"
        assert parsed_message.body == b"Wikipedia in\r\n\r\nchunks."
