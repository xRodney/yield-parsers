import delimiting_parser
from parser_utils import parse


def test_whole_sentences():
    parser = delimiting_parser.prepare(".")
    results = []
    next(parser)

    results += parse(parser, "first.second.")
    results += parse(parser, "third.forth.")

    assert results == ["first", "second", "third", "forth"]


def test_one():
    parser = delimiting_parser.prepare(".")
    results = []
    next(parser)

    results += parse(parser, "first.second.third.forth.")

    assert results == ["first", "second", "third", "forth"]


def test_split():
    parser = delimiting_parser.prepare(".")
    results = []
    next(parser)

    results += parse(parser, "fi")
    results += parse(parser, "rs")
    results += parse(parser, "t.sec")
    results += parse(parser, "ond.")
    results += parse(parser, "third.forth.")

    assert results == ["first", "second", "third", "forth"]
