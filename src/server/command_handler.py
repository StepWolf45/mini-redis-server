"""
Обработчик команд: маршрутизация имен.
"""
from typing import Dict, List, Tuple, Any

from .storage import Storage
from .commands.base_abstraction import Command, get_registered_commands
# Импорт модулей команд для регистрации


class CommandFactory:
    """Фабрика для создания экземпляров команд с зависимостями."""

    def __init__(self, storage: Storage):
        self.storage = storage

    def create_command(self, command_cls: type[Command]) -> Command:
        """Создает экземпляр команды с необходимыми зависимостями."""
        return command_cls(self.storage)


class CommandHandler:
    """Регистрирует и выполняет команды по имени."""

    def __init__(self, storage: Storage):
        self._storage = storage
        self._commands: Dict[str, Command] = {}
        self._factory = CommandFactory(storage)
        self._register_defaults()

    def _register_defaults(self) -> None:
        registry = get_registered_commands()
        self._commands = {
            name: self._factory.create_command(command_cls)
            for name, command_cls in registry.items()
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


