"""
This is a first generator-based parser
"""


def prepare(delimiter):
    data = yield None
    while True:
        index = data.find(delimiter)
        if index >= 0:
            result = data[:index]
            data = data[index + 1:]
        else:
            result = None

        moredata = yield result

        if moredata:
            data = data + moredata
