from src.server.commands.base_abstraction import Command


class Dummy(Command):
    def execute(self, args):
        return True, args

    def get_name(self):
        return "DUMMY"


def test_validate_args_bounds():
    """Тест валидации количества аргументов в методе validate_args."""
    assert Command.validate_args(["a"], 1, 2) is True
    assert Command.validate_args(["a", "b"], 1, 2) is True
    assert Command.validate_args([], 1, 2) is False
    assert Command.validate_args(["a", "b", "c"], 1, 2) is False



