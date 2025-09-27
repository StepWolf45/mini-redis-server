"""
Пример использования Redis клиента.
"""
import sys
import os

# Добавляем src в путь
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from client import RedisClient


def main():
    """Демонстрация работы клиента."""

    print("Mini Redis Client Demo")
    print("=" * 40)
    # Создаем клиент
    client = RedisClient(host='localhost', port=6379)

    try:
        # Подключаемся
        if not client.connect():
            print("ERROR: Не удалось подключиться к серверу")
            return

        print("Connected to server localhost:6379")

        print("\nTesting commands:")
        # SET
        try:
            success = client.set("demo_key", "demo_value", ex=30)
            print(f"SET demo_key: {'OK' if success else 'FAILED'}")
        except Exception as e:
            print(f"SET error: {e}")

        # GET
        try:
            value = client.get("demo_key")
            print(f"GET demo_key: {value}")
        except Exception as e:
            print(f"GET error: {e}")

        # TTL
        try:
            ttl = client.ttl("demo_key")
            print(f"TTL demo_key: {ttl} sec")
        except Exception as e:
            print(f"TTL error: {e}")

        # EXISTS
        try:
            exists = client.exists("demo_key", "nonexistent")
            print(f"EXISTS demo_key, nonexistent: {exists}")
        except Exception as e:
            print(f"EXISTS error: {e}")

        # KEYS
        try:
            keys = client.keys("*")
            print(f"KEYS *: {keys}")
        except Exception as e:
            print(f"KEYS error: {e}")

        # DEL
        try:
            deleted = client.delete("demo_key")
            print(f"DEL demo_key: {deleted} keys deleted")
        except Exception as e:
            print(f"DEL error: {e}")

        print("\nDemo completed successfully!")

    except Exception as e:
        print(f"ERROR: {e}")
    finally:
        client.disconnect()


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] in ['-h', '--help']:
        print("Использование: python example_client.py")
        print("Убедитесь, что сервер запущен на localhost:6379")
        sys.exit(0)

    main()