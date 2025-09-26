"""
Базовые интерфейсы и утилиты для команд.
Позволяет серверу работать c командами полиморфно.
"""
from abc import ABC, abstractmethod
from typing import Any, List, Tuple


class Command(ABC):
    """Абстрактная команда Redis-подобного севера."""

    @abstractmethod
    def execute(self, args: List[str]) -> Tuple[bool, Any]:
        """
        Выполняет команду c аргументами.

        Возвращает (успех, результат||сообщение об ошибке)
        """
        raise NotImplementedError

    @abstractmethod
    def get_name(self) -> str:
        """Имя команды"""
        raise NotImplementedError

    @staticmethod
    def validate_args(args: List[str], min_args: int, max_args: int | None = None) -> bool:
        """
        Проверяет, что число аргументов в допустимых границах.
        """
        if len(args) < min_args:
            return False
        if max_args is not None and len(args) > max_args:
            return False
        return True


