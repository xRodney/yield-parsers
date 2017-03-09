CRLF = "\r\n"


def prepare():
    data = yield None
    while True:
        first_line, data = yield from get_line(data)
        count = int(first_line)

        msg, data = yield from get_bytes(data, count)
        data = yield from get_more(data, msg)


def get_line(data):
    index = -1
    while index < 0:
        index = data.find(CRLF)
        if index < 0:
            data = yield from get_more(data)

    return data[:index], data[index + 2:]


def get_bytes(data, count):
    while (len(data) < count):
        data = yield from get_more(data)

    return data[:count], data[count:]


def get_more(data, result=None):
    moredata = yield result
    return data + moredata if moredata else data
