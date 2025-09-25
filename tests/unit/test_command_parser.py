from src.server.command_parser import CommandParser


def test_parse_command_basic():
    assert CommandParser.parse_command("SET a 1") == ["SET", "a", "1"]
    assert CommandParser.parse_command("  GET   a  ") == ["GET", "a"]
    assert CommandParser.parse_command("") == []


def test_format_response_scalars():
    assert CommandParser.format_response(None) == "$-1\r\n"
    assert CommandParser.format_response(5) == ":5\r\n"
    assert CommandParser.format_response(True) == ":1\r\n"
    assert CommandParser.format_response(False) == ":0\r\n"
    assert CommandParser.format_response("ok") == "$2\r\nok\r\n"


def test_format_response_list():
    res = CommandParser.format_response(["a", 2, None])
    assert res.startswith("*3\r\n")


def test_format_error_and_ok():
    assert CommandParser.format_error("ERR") == "-ERR\r\n"
    assert CommandParser.format_ok() == "+OK\r\n"


