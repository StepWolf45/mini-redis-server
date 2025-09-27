from src.server.command_parser import CommandParser


def test_parse_command_basic():
    """Тест базового парсинга командной строки."""
    assert CommandParser.parse_command("SET a 1") == ["SET", "a", "1"]
    assert CommandParser.parse_command("  GET   a  ") == ["GET", "a"]
    assert CommandParser.parse_command("") == []


def test_format_response_scalars():
    """Тест форматирования скалярных значений в RESP."""
    assert CommandParser.format_response(None) == "$-1\r\n"
    assert CommandParser.format_response(5) == ":5\r\n"
    assert CommandParser.format_response(True) == ":1\r\n"
    assert CommandParser.format_response(False) == ":0\r\n"
    assert CommandParser.format_response("ok") == "$2\r\nok\r\n"
    assert CommandParser.format_response(3.14) == "$4\r\n3.14\r\n"
    assert CommandParser.format_response({"key": "value"}) == "$16\r\n{'key': 'value'}\r\n"


def test_format_response_list():
    """Тест форматирования списков в RESP."""
    res = CommandParser.format_response(["a", 2, None])
    assert res.startswith("*3\r\n")


def test_format_error_and_ok():
    """Тест форматирования ошибок и OK ответов."""
    assert CommandParser.format_error("ERR") == "-ERR\r\n"
    assert CommandParser.format_ok() == "+OK\r\n"


def test_parse_command_with_quotes():
    """Тест парсинга inline-команд с кавычками."""
    assert CommandParser.parse_command('SET key "hello world"') == ["SET", "key", "hello world"]
    assert CommandParser.parse_command("SET key 'single quotes'") == ["SET", "key", "single quotes"]
    assert CommandParser.parse_command("SET key value") == ["SET", "key", "value"]
    assert CommandParser.parse_command("") == []


