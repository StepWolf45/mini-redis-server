from src.server.commands.set import SetCommand
from src.server.commands.get import GetCommand
from src.server.storage import Storage


def test_set_command_basic():
    """Тест базовой функциональности SET."""
    storage = Storage()
    cmd = SetCommand(storage)
    
    # Успешная установка
    success, result = cmd.execute(["key1", "value1"])
    assert success is True
    assert result == "OK"
    
    # Проверяем, что значение сохранилось
    found, value = storage.get("key1")
    assert found is True
    assert value == "value1"


def test_set_command_with_ttl():
    """Тест SET с TTL."""
    storage = Storage()
    cmd = SetCommand(storage)
    
    # SET с EX (секунды)
    success, result = cmd.execute(["temp", "data", "EX", "1"])
    assert success is True
    assert result == "OK"
    
    # Проверяем TTL
    ttl = storage.ttl("temp")
    assert 0 <= ttl <= 1
    
    # SET с PX (миллисекунды)
    success, result = cmd.execute(["temp2", "data2", "PX", "500"])
    assert success is True
    assert result == "OK"
    
    ttl = storage.ttl("temp2")
    assert 0 <= ttl <= 0.5


def test_set_command_validation():
    """Тест валидации аргументов SET."""
    storage = Storage()
    cmd = SetCommand(storage)
    
    # Недостаточно аргументов
    success, result = cmd.execute(["key"])
    assert success is False
    assert "wrong number of arguments" in result
    
    # Неверный EX
    success, result = cmd.execute(["key", "value", "EX", "invalid"])
    assert success is False
    assert "value is not an integer" in result
    
    # Отрицательный TTL
    success, result = cmd.execute(["key", "value", "EX", "-1"])
    assert success is False
    assert "invalid expire time" in result
    
    # Неизвестный аргумент
    success, result = cmd.execute(["key", "value", "UNKNOWN", "1"])
    assert success is False
    assert "unknown option" in result


def test_get_command_basic():
    """Тест базовой функциональности GET."""
    storage = Storage()
    cmd = GetCommand(storage)
    
    # Получение существующего ключа
    storage.set("key1", "value1")
    success, result = cmd.execute(["key1"])
    assert success is True
    assert result == "value1"
    
    # Получение несуществующего ключа
    success, result = cmd.execute(["nonexistent"])
    assert success is True
    assert result is None


def test_get_command_validation():
    """Тест валидации аргументов GET."""
    storage = Storage()
    cmd = GetCommand(storage)
    
    # Недостаточно аргументов
    success, result = cmd.execute([])
    assert success is False
    assert "wrong number of arguments" in result
    
    # Слишком много аргументов
    success, result = cmd.execute(["key1", "extra"])
    assert success is False
    assert "wrong number of arguments" in result


def test_commands_with_shared_storage():
    """Интеграционный тест SET + GET."""
    storage = Storage()
    set_cmd = SetCommand(storage)
    get_cmd = GetCommand(storage)
    
    # Устанавливаем значение
    success, result = set_cmd.execute(["test", "hello"])
    assert success is True
    
    # Получаем значение
    success, result = get_cmd.execute(["test"])
    assert success is True
    assert result == "hello"
    
    # Перезаписываем значение
    success, result = set_cmd.execute(["test", "world"])
    assert success is True
    
    # Проверяем новое значение
    success, result = get_cmd.execute(["test"])
    assert success is True
    assert result == "world"
