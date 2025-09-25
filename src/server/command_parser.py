"""
Парсер команд Redis-подобного протокола.
"""
from typing import Any, List


class CommandParser:
    """Простой парсер команд и форматировщик ответов в стиле RESP."""

    @staticmethod
    def parse_command(data: str) -> List[str]:
        """
        Парсит команду из строки: разделение по пробелам, обрезка краёв.

        Пример: "SET key value" -> ["SET", "key", "value"]
        """
        parts = data.strip().split()
        return parts if parts else []

    @staticmethod
    def format_response(value: Any) -> str:
        """
        Форматирует значение в упрощённом RESP:
        - None -> "$-1\r\n"
        - int/bool -> ":<num>\r\n"
        - str -> "$<len>\r\n<str>\r\n"
        - list -> массив из элементов (рекурсивно)
        Остальные типы -> str(value) как bulk string
        """
        if value is None:
            return "$-1\r\n"

        if isinstance(value, bool):
            return f":{1 if value else 0}\r\n"

        if isinstance(value, int):
            return f":{value}\r\n"

        if isinstance(value, str):
            return f"${len(value)}\r\n{value}\r\n"

        if isinstance(value, list):
            result = f"*{len(value)}\r\n"
            for item in value:
                result += CommandParser.format_response(item)
            return result

        text = str(value)
        return f"${len(text)}\r\n{text}\r\n"

    @staticmethod
    def format_error(message: str) -> str:
        return f"-{message}\r\n"

    @staticmethod
    def format_ok() -> str:
        return "+OK\r\n"


