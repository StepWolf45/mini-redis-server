# Mini Redis Server

Простая реализация Redis-совместимого сервера на Python с поддержкой основных команд и TTL.

### Локальный запуск

```bash
# Установка зависимостей
pip install -r requirements.txt

# Запуск сервера
python entrypoint.py

# Или через модуль
python -m src.server.tcp_server
```
Сервер запустится на порту 6379 (стандартный Redis порт).

### Запуск через Docker

```bash

# Сборка образа
docker build -t mini-redis-server .

# Запуск контейнера
docker run -p 6379:6379 mini-redis-server

# Или с кастомными переменными окружения
docker run -p 6379:6379 -e REDIS_HOST=0.0.0.0 -e REDIS_PORT=6379 mini-redis-server
```

## Переменные окружения

- `REDIS_HOST` - хост для привязки сервера (по умолчанию: `0.0.0.0` в Docker, `127.0.0.1` локально)
- `REDIS_PORT` - порт сервера (по умолчанию: `6379`)

## Тестирование

```bash
# Запуск всех тестов
python -m pytest

# Запуск с покрытием
python -m pytest --cov=src --cov-report=term-missing

# Запуск конкретных тестов
python -m pytest tests/unit/test_storage.py -v
python -m pytest tests/integration/test_tcp_server.py -v
```

## Подключение клиентов

### Через telnet
```bash
telnet localhost 6379
SET hello world
GET hello
```

### Через Redis CLI (если установлен)
```bash
redis-cli -p 6379
SET key value
GET key
```

### Через Python клиент
```python
# Простой способ
import socket

def send_command(command):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(('localhost', 6379))
    sock.send(f"{command}\r\n".encode())
    response = sock.recv(1024).decode()
    sock.close()
    return response

print(send_command("SET test hello"))  # +OK
print(send_command("GET test"))        # $5\r\nhello\r\n

# Или используйте готовый клиент
from src.client import RedisClient

with RedisClient() as client:
    client.set("key", "value", ex=60)
    value = client.get("key")
    print(f"Value: {value}")

# Запустите демо клиента
python example_client.py
```

## Документация

- [Описание команд](docs/commands.md)
- [Расширяемость решения](docs/extensibility.md)
- [Альтернативы и выбор решения](docs/alternatives.md)
- [Тест-кейсы](tests/test_cases.md)

