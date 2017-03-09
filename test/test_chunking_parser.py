import chunking_parser
from parser_utils import parse


def test_one():
    parser = chunking_parser.prepare()
    results = []
    next(parser)

    results += parse(parser, "5\r\nabcdeXX")

    assert results == ["abcde"]


def test_one_split():
    parser = chunking_parser.prepare()
    results = []
    next(parser)

    results += parse(parser, "5\r")
    results += parse(parser, "\nabc")
    results += parse(parser, "deXX")

    assert results == ["abcde"]


def test_multiple():
    parser = chunking_parser.prepare()
    results = []
    next(parser)

    results += parse(parser, "5\r")
    results += parse(parser, "\nabc")
    results += parse(parser, "de2\r\nXX")

    assert results == ["abcde", "XX"]
