from src.server.commands.ttl import TtlCommand, ExpireCommand, ExistsCommand, DelCommand, KeysCommand
from src.server.storage import Storage


def test_ttl_command():
    """Тест команды TTL."""
    storage = Storage()
    cmd = TtlCommand(storage)
    
    # Несуществующий ключ
    success, result = cmd.execute(["nonexistent"])
    assert success is True
    assert result == -2
    
    # Бессрочный ключ
    storage.set("permanent", "value")
    success, result = cmd.execute(["permanent"])
    assert success is True
    assert result == -1
    
    # Ключ с TTL
    storage.set("temp", "value", ttl=1.0)
    success, result = cmd.execute(["temp"])
    assert success is True
    assert 0 <= result <= 1


def test_expire_command():
    """Тест команды EXPIRE."""
    storage = Storage()
    cmd = ExpireCommand(storage)
    
    # Устанавливаем TTL для существующего ключа
    storage.set("key", "value")
    success, result = cmd.execute(["key", "1"])
    assert success is True
    assert result == 1
    
    # Проверяем TTL
    ttl = storage.ttl("key")
    assert 0 <= ttl <= 1
    
    # Несуществующий ключ
    success, result = cmd.execute(["nonexistent", "1"])
    assert success is True
    assert result == 0
    
    # Неверные аргументы
    success, result = cmd.execute(["key"])
    assert success is False
    assert "wrong number of arguments" in result
    
    # Неверное время
    success, result = cmd.execute(["key", "invalid"])
    assert success is False
    assert "value is not an integer" in result


def test_exists_command():
    """Тест команды EXISTS."""
    storage = Storage()
    cmd = ExistsCommand(storage)
    
    # Создаем ключи
    storage.set("key1", "value1")
    storage.set("key2", "value2")
    
    # Проверяем один ключ
    success, result = cmd.execute(["key1"])
    assert success is True
    assert result == 1
    
    # Проверяем несколько ключей
    success, result = cmd.execute(["key1", "key2", "nonexistent"])
    assert success is True
    assert result == 2
    
    # Недостаточно аргументов
    success, result = cmd.execute([])
    assert success is False
    assert "wrong number of arguments" in result


def test_del_command():
    """Тест команды DEL."""
    storage = Storage()
    cmd = DelCommand(storage)
    
    # Создаем ключи
    storage.set("key1", "value1")
    storage.set("key2", "value2")
    
    # Удаляем один ключ
    success, result = cmd.execute(["key1"])
    assert success is True
    assert result == 1
    
    # Проверяем, что ключ удален
    assert not storage.exists("key1")
    assert storage.exists("key2")
    
    # Удаляем несколько ключей
    success, result = cmd.execute(["key2", "nonexistent"])
    assert success is True
    assert result == 1  # только key2 был удален
    
    # Недостаточно аргументов
    success, result = cmd.execute([])
    assert success is False
    assert "wrong number of arguments" in result


def test_keys_command():
    """Тест команды KEYS."""
    storage = Storage()
    cmd = KeysCommand(storage)
    
    # Создаем ключи
    storage.set("user:1", "alice")
    storage.set("user:2", "bob")
    storage.set("session:abc", "data")
    
    # Получаем все ключи
    success, result = cmd.execute(["*"])
    assert success is True
    assert len(result) == 3
    assert "user:1" in result
    assert "user:2" in result
    assert "session:abc" in result
    
    # Недостаточно аргументов
    success, result = cmd.execute([])
    assert success is False
    assert "wrong number of arguments" in result


def test_ttl_workflow():
    """Интеграционный тест TTL workflow."""
    storage = Storage()
    ttl_cmd = TtlCommand(storage)
    expire_cmd = ExpireCommand(storage)
    exists_cmd = ExistsCommand(storage)
    
    # Создаем ключ
    storage.set("test", "value")
    
    # Проверяем, что ключ существует
    success, result = exists_cmd.execute(["test"])
    assert success is True
    assert result == 1
    
    # Устанавливаем TTL
    success, result = expire_cmd.execute(["test", "0.1"])
    assert success is True
    assert result == 1
    
    # Проверяем TTL
    success, result = ttl_cmd.execute(["test"])
    assert success is True
    assert 0 <= result <= 0.1
    
    # Ждем истечения
    import time
    time.sleep(0.15)
    
    # Проверяем, что ключ истек
    success, result = exists_cmd.execute(["test"])
    assert success is True
    assert result == 0
