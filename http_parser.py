from parser_utils import get_bytes, get_more, get_word, get_rest, get_until

CRLF = "\r\n"


class HttpMessage:
    def __init__(self):
        self.body = None


class HttpRequest(HttpMessage):
    def __init__(self):
        super().__init__()

    def has_body(self):
        return self.method in ("POST", "PUT", "PATCH")


class HttpResponse(HttpMessage):
    def __init__(self):
        super().__init__()

    def has_body(self):
        return self.status in ("200", "404")  # TODO: Add all codes that have bodies


def bytes_to_str(b):
    return str(b, 'latin1')


def get_http_request(data):
    message, data = yield from get_firstline(data)
    message.headers, data = yield from get_headers(data)
    if message.has_body():
        if "Content-Length" in message.headers:
            message.body, data = yield from get_bytes(data, int(message.headers["Content-Length"]))
        elif message.headers.get("Transfer-Encoding", None) == "chunked":
            message.body, data = yield from get_chunked_body(data)
            # TODO: Parse trailing headers
        else:
            message.body, data = yield from get_rest(data)

    return message, data


def get_line(data):
    return get_until(data, b"\r\n")


def parse_http_version(method):
    if method[:5] == b"HTTP/":
        version = method[5:]
        return [bytes_to_str(x) for x in version.split(b".")]
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

        response.status = bytes_to_str(response.status)
        response.status_message = bytes_to_str(response.status_message)

        return response, data
    else:
        request = HttpRequest()
        request.method = bytes_to_str(method)
        path, data = yield from get_word(data)
        request.path = bytes_to_str(path)
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
            headers[bytes_to_str(name)] = bytes_to_str(value).lstrip()
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
