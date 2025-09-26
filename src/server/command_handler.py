"""
Обработчик команд: маршрутизация имен.
"""
from typing import Dict, List, Tuple, Any

from .storage import Storage
from .commands.base_abstraction import Command
from .commands.get import GetCommand
from .commands.set import SetCommand
from .commands.ttl import (
    TtlCommand,
    ExpireCommand,
    ExistsCommand,
    DelCommand,
    KeysCommand,
)


class CommandHandler:
    """Регистрирует и выполняет команды по имени."""

    def __init__(self, storage: Storage):
        self._storage = storage
        self._commands: Dict[str, Command] = {}
        self._register_defaults()

    def _register_defaults(self) -> None:
        self._commands = {
            "GET": GetCommand(self._storage),
            "SET": SetCommand(self._storage),
            "TTL": TtlCommand(self._storage),
            "EXPIRE": ExpireCommand(self._storage),
            "EXISTS": ExistsCommand(self._storage),
            "DEL": DelCommand(self._storage),
            "KEYS": KeysCommand(self._storage),
        }

    def handle(self, command_name: str, args: List[str]) -> Tuple[bool, Any]:
        name = command_name.upper()
        command = self._commands.get(name)
        if command is None:
            return False, f"ERR: unknown command '{name}'"
        try:
            return command.execute(args)
        except Exception as exc: 
            return False, f"ERR: {exc}"

    def register(self, name: str, command: Command) -> None:
        self._commands[name.upper()] = command

    def available(self) -> List[str]:
        return list(self._commands.keys())


