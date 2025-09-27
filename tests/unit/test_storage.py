import asyncio
import time

from src.server.storage import Storage


def test_set_and_get_without_ttl():
    """Тест установки и получения значения ключа без TTL."""
    storage = Storage()
    assert storage.set("key1", "value1") is True
    found, value = storage.get("key1")
    assert found is True
    assert value == "value1"


def test_get_non_existing_key_returns_none():
    """Тест получения значения для несуществующего ключа."""
    storage = Storage()
    found, value = storage.get("absent")
    assert found is False
    assert value is None


def test_set_with_ttl_and_expire_automatically():
    """Тест установки значения с TTL и автоматического истечения."""
    storage = Storage()

    async def scenario():
        await storage.start_cleanup_task()
        try:
            assert storage.set("temp", "v", ttl=0.2) is True
            found, value = storage.get("temp")
            assert found is True and value == "v"

            await asyncio.sleep(0.35)

            found, value = storage.get("temp")
            assert found is False and value is None
        finally:
            await storage.stop_cleanup_task()

    asyncio.run(scenario())


def test_expire_existing_key():
    """Тест установки TTL для существующего ключа через EXPIRE."""
    storage = Storage()
    storage.set("k", "v")
    assert storage.expire("k", 0.1) is True
    assert storage.ttl("k") >= 0
    time.sleep(0.15)

    found, _ = storage.get("k")
    assert found is False


def test_ttl_values():
    """Тест возврата TTL для различных типов ключей."""
    storage = Storage()
    # несуществующий ключ
    assert storage.ttl("nope") == -2

    # бессрочный ключ
    storage.set("permanent", "v")
    assert storage.ttl("permanent") == -1

    # ключ с TTL
    storage.set("t", "v", ttl=1)
    ttl_value = storage.ttl("t")
    assert 0 <= ttl_value <= 1


def test_exists_and_delete():
    """Тест методов exists и delete."""
    storage = Storage()
    storage.set("a", "1")
    assert storage.exists("a") is True
    assert storage.delete("a") is True
    assert storage.exists("a") is False
    assert storage.delete("a") is False


def test_keys_and_size_with_expired_entries():
    """Тест методов keys и size с автоматической очисткой истекших ключей."""
    storage = Storage()
    storage.set("k1", "v1")
    storage.set("k2", "v2", ttl=0.1)
    storage.set("other", "v3")

    keys = storage.keys("*")
    assert set(keys) >= {"k1", "k2", "other"}

    time.sleep(0.15)

    size_before = storage.size()
    keys_after = storage.keys("*")
    assert "k2" not in keys_after
    assert size_before == len(keys_after)


def test_heap_based_cleanup_efficiency():
    """Тест, что heap позволяет эффективно удалять только истекшие ключи."""
    storage = Storage()

    async def scenario():
        await storage.start_cleanup_task()
        try:
            # Устанавливаем ключи с разными TTL
            storage.set("short", "v1", ttl=0.1)
            storage.set("medium", "v2", ttl=0.3)
            storage.set("long", "v3", ttl=1.0)
            storage.set("permanent", "v4")  # без TTL

            # Проверяем, что все ключи существуют
            assert storage.exists("short") is True
            assert storage.exists("medium") is True
            assert storage.exists("long") is True
            assert storage.exists("permanent") is True

            # Ждем истечения short
            await asyncio.sleep(0.15)

            # short должен быть удален, остальные нет
            assert storage.exists("short") is False
            assert storage.exists("medium") is True
            assert storage.exists("long") is True
            assert storage.exists("permanent") is True

            # Ждем истечения medium
            await asyncio.sleep(0.2)

            assert storage.exists("medium") is False
            assert storage.exists("long") is True
            assert storage.exists("permanent") is True

        finally:
            await storage.stop_cleanup_task()

    asyncio.run(scenario())


def test_ttl_update_in_heap():
    """Тест, что обновление TTL правильно обновляет heap."""
    storage = Storage()

    async def scenario():
        await storage.start_cleanup_task()
        try:
            storage.set("key", "value", ttl=0.1)
            assert storage.expire("key", 1.0) is True
            await asyncio.sleep(0.2)
            assert storage.exists("key") is True

        finally:
            await storage.stop_cleanup_task()

    asyncio.run(scenario())


def test_clear_resets_heap():
    """Тест, что clear очищает и данные, и heap."""
    storage = Storage()
    storage.set("k1", "v1", ttl=1.0)
    storage.set("k2", "v2")

    assert len(storage._expire_heap) > 0

    storage.clear()

    assert len(storage._data) == 0
    assert len(storage._expire_heap) == 0


def test_match_pattern():
    """Тест сопоставления паттернов."""
    storage = Storage()

    # Тесты для _match_pattern
    assert storage._match_pattern("key1", "*") is True
    assert storage._match_pattern("key1", "key1") is True
    assert storage._match_pattern("key1", "key?") is True
    assert storage._match_pattern("key1", "key2") is False
    assert storage._match_pattern("key1", "k*") is True
    assert storage._match_pattern("key1", "*1") is True


def test_storage_exception_in_ttl():
    """Тест исключений в ttl."""
    storage = Storage()

    # Создаем ключ с TTL
    storage.set("key", "value", ttl=0.1)

    # Ждем истечения
    import time
    time.sleep(0.15)

    # ttl должен вернуть -2 для истекшего ключа
    result = storage.ttl("key")
    assert result == -2


def test_storage_exception_in_expire():
    """Тест исключений в expire."""
    storage = Storage()

    # Создаем ключ с TTL
    storage.set("key", "value", ttl=0.1)

    # Ждем истечения
    import time
    time.sleep(0.15)

    # expire на истекший ключ должен вернуть False
    result = storage.expire("key", 1.0)
    assert result is False


def test_storage_keys_with_pattern():
    """Тест keys с паттерном."""
    storage = Storage()
    storage.set("user1", "a")
    storage.set("user2", "b")
    storage.set("admin", "c")

    # Паттерн user*
    result = storage.keys("user*")
    assert set(result) == {"user1", "user2"}


