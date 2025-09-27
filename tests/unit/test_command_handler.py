"""Тесты для CommandHandler, регистрации команд и фабрики."""
from src.server.command_handler import CommandHandler, CommandFactory
from src.server.storage import Storage
from src.server.commands.base_abstraction import get_registered_commands, register_command, Command


@register_command("TEST_CMD")
class TestCommand(Command):
    """Тестовая команда для проверки регистрации."""

    def __init__(self, storage):
        self.storage = storage

    def execute(self, args):
        return True, f"test_result_{len(args)}"

    def get_name(self):
        return "TEST_CMD"


def test_command_registration():
    """Тест автоматической регистрации команд через декоратор."""
    registry = get_registered_commands()
    assert "TEST_CMD" in registry
    assert registry["TEST_CMD"] == TestCommand


def test_command_factory():
    """Тест фабрики команд."""
    storage = Storage()
    factory = CommandFactory(storage)

    cmd = factory.create_command(TestCommand)
    assert isinstance(cmd, TestCommand)
    assert cmd.storage is storage

    success, result = cmd.execute(["arg1", "arg2"])
    assert success is True
    assert result == "test_result_2"


def test_command_handler_registration():
    """Тест регистрации команд в CommandHandler."""
    storage = Storage()
    handler = CommandHandler(storage)


    available = handler.available()
    assert "TEST_CMD" in available


    success, result = handler.handle("TEST_CMD", ["test"])
    assert success is True
    assert result == "test_result_1"


def test_command_handler_unknown_command():
    """Тест обработки неизвестной команды."""
    storage = Storage()
    handler = CommandHandler(storage)

    success, result = handler.handle("UNKNOWN", [])
    assert success is False
    assert "unknown command" in result


def test_command_handler_with_existing_commands():
    """Тест, что существующие команды работают через handler."""
    storage = Storage()
    handler = CommandHandler(storage)

    success, result = handler.handle("SET", ["key", "value"])
    assert success is True
    assert result == "OK"

    success, result = handler.handle("GET", ["key"])
    assert success is True
    assert result == "value"


def test_command_handler_exception_in_handle():
    """Тест обработки исключений в handle"""
    storage = Storage()
    handler = CommandHandler(storage)

    class MockCommand:
        def execute(self, args):
            raise Exception("Mock error")

    handler._commands["MOCK"] = MockCommand()

    success, result = handler.handle("MOCK", [])
    assert success is False
    assert "ERR: Mock error" in result


def test_command_handler_exception_handling():
    """Тест обработки исключений в командах."""
    storage = Storage()
    handler = CommandHandler(storage)

    @register_command("ERROR_CMD")
    class ErrorCommand(Command):
        def __init__(self, storage):
            self.storage = storage

        def execute(self, args):
            raise ValueError("Test error")

        def get_name(self):
            return "ERROR_CMD"

    handler._commands["ERROR_CMD"] = ErrorCommand(storage)

    success, result = handler.handle("ERROR_CMD", [])
    assert success is False
    assert "ERR: Test error" in result