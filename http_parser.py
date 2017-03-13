from parser_utils import get_bytes, get_more, get_word, get_rest, get_until

CRLF = "\r\n"


class HttpMessage:
    def __init__(self):
        self.version = None
        self.headers = dict()
        self.body = None

    def is_text(self):
        content_type = self.headers.get(b"Content-Type", b"")
        return b"text" in content_type or b"xml" in content_type

    def __str__(self):
        data = self.first_line().decode()
        for name, value in self.headers.items():
            data += "%s: %s\r\n" % (name.decode(), value.decode())
        data += "\r\n"
        if self.has_body():
            if not self.is_text():
                data += self.body.hex() + "\n"
            else:
                data += str(self.body[:75]) + (self.body[75:] and '... (truncated)')
                data += "\n"

        return data

    def to_bytes(self):
        data = self.first_line()
        yield data
        for name, value in self.headers.items():
            yield b"%s: %s\r\n" % (name, value)
        yield b"\r\n"
        if self.has_body():
            yield self.body

    def has_body(self):
        pass

    def first_line(self):
        pass


class HttpRequest(HttpMessage):
    def __init__(self):
        super().__init__()
        self.method = None
        self.path = None

    def has_body(self):
        return self.method in (b"POST", b"PUT", b"PATCH")

    def first_line(self):
        return b"%s %s %s\r\n" % (self.method, self.path, self.version)


class HttpResponse(HttpMessage):
    def __init__(self):
        super().__init__()
        self.status_message = None
        self.status = None

    def has_body(self):
        return self.status in (b"200", b"404")  # TODO: Add all codes that have bodies

    def first_line(self):
        return b"%s %s %s\r\n" % (self.version, self.status, self.status_message)


def get_http_request(data):
    message, data = yield from get_firstline(data)
    message.headers, data = yield from get_headers(data)
    if message.has_body():
        if b"Content-Length" in message.headers:
            message.body, data = yield from get_bytes(data, int(message.headers[b"Content-Length"]))
        elif message.headers.get(b"Transfer-Encoding", None) == b"chunked":
            message.body, data = yield from get_chunked_body(data)
            # TODO: Parse trailing headers
        else:
            message.body, data = yield from get_rest(data)

    return message, data


def get_line(data):
    return get_until(data, b"\r\n")


def parse_http_version(version):
    if version[:5] == b"HTTP/":
        return version
    else:
        return None


def get_firstline(data):
    method, data = yield from get_word(data)
    method = method.upper()
    version = parse_http_version(method)
    if version:
        response = HttpResponse()
        response.version = version
        response.status, data = yield from get_word(data)
        response.status_message, data = yield from get_line(data)

        response.status = response.status
        response.status_message = response.status_message

        return response, data
    else:
        request = HttpRequest()
        request.method = method
        path, data = yield from get_word(data)
        request.path = path
        version_str, data = yield from get_word(data)
        request.version = parse_http_version(version_str)
        return request, data


def get_headers(data):
    headers = {}
    line, data = yield from get_line(data)
    name = None
    value = None
    while line:
        if line[0] in (b" ", b"\t") and name:
            # TODO: Double check this logic here, it may leave unwanted characters
            value = value + line
            headers[name] = value
        else:
            name, value = line.split(b":", 1)
            headers[name] = value.lstrip()
        line, data = yield from get_line(data)

    return headers, data


def get_chunked_body(data):
    chunk_size, data = yield from get_line(data)
    chunk_size = int(chunk_size, 16)
    body = []
    while chunk_size > 0:
        chunk, data = yield from get_bytes(data, int(chunk_size))
        body.append(chunk)
        _, data = yield from get_line(data)  # read the trailing CRLF
        chunk_size, data = yield from get_line(data)
        chunk_size = int(chunk_size, 16)

    assert chunk_size == 0
    _, data = yield from get_line(data)  # read the trailing CRLF

    return b"".join(body), data
