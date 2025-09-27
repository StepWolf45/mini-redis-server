"""
Redis-совместимый клиент для mini-redis-server.
"""
import socket
import time
from typing import Any, Optional, Union, List


class RedisClient:
    """
    Поддерживает основные команды Redis с автоматическим парсингом ответов.
    """

    def __init__(self, host: str = 'localhost', port: int = 6379, timeout: float = 5.0):
        """
        Инициализация клиента.

        Args:
            host: Хост сервера
            port: Порт сервера
            timeout: Таймаут соединения в секундах
        """
        self.host = host
        self.port = port
        self.timeout = timeout
        self._socket: Optional[socket.socket] = None
        self._connected = False

    def connect(self) -> bool:
        """
        Подключение к серверу.

        Returns:
            True если подключение успешно
        """
        try:
            self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._socket.settimeout(self.timeout)
            self._socket.connect((self.host, self.port))
            self._connected = True
            return True
        except Exception as e:
            print(f"Connection failed: {e}")
            self._connected = False
            return False

    def disconnect(self):
        """Отключение от сервера."""
        if self._socket:
            try:
                self._socket.close()
            except:
                pass
        self._socket = None
        self._connected = False

    def _send_command(self, command: str) -> str:
        """
        Отправка команды серверу.

        Args:
            command: Команда в формате inline

        Returns:
            Ответ сервера как строка
        """
        if not self._connected or not self._socket:
            raise ConnectionError("Not connected to server")

        try:
            self._socket.send(f"{command}\r\n".encode())

            response = b""
            while True:
                chunk = self._socket.recv(1024)
                if not chunk:
                    break
                response += chunk
                if response.endswith(b"\r\n"):
                    break

            return response.decode('utf-8', errors='replace').strip()

        except Exception as e:
            raise ConnectionError(f"Command failed: {e}")

    def _parse_response(self, response: str) -> Any:
        """
        Парсинг ответа сервера в формате RESP.

        Args:
            response: Ответ сервера

        Returns:
            Распарсенное значение
        """
        if not response:
            return None

        # Обработка простых строк
        if response.startswith('+'):
            return response[1:] 

        # Обработка ошибок
        if response.startswith('-'):
            raise RedisError(response[1:])

        # Обработка целых чисел
        if response.startswith(':'):
            try:
                return int(response[1:])
            except ValueError:
                return response[1:]

        # Обработка bulk strings
        if response.startswith('$'):
            lines = response.split('\r\n')
            if len(lines) >= 2:
                try:
                    length = int(lines[0][1:])
                    if length == -1:
                        return None
                    return lines[1]
                except (ValueError, IndexError):
                    pass

        # Обработка массивов (упрощенная)
        if response.startswith('*'):
            lines = response.split('\r\n')
            if len(lines) >= 2:
                try:
                    count = int(lines[0][1:])
                    result = []
                    idx = 1
                    for _ in range(count):
                        if idx + 1 < len(lines):

                            result.append(lines[idx + 1])
                            idx += 2
                    return result
                except (ValueError, IndexError):
                    pass


        return response

    # Команды Redis
    def set(self, key: str, value: Any, ex: Optional[int] = None, px: Optional[int] = None) -> bool:
        """
        SET команда.

        Args:
            key: Ключ
            value: Значение
            ex: TTL в секундах
            px: TTL в миллисекундах

        Returns:
            True если успешно
        """
        cmd = f"SET {key} {value}"
        if ex is not None:
            cmd += f" EX {ex}"
        elif px is not None:
            cmd += f" PX {px}"

        response = self._send_command(cmd)
        result = self._parse_response(response)
        return result == "OK"

    def get(self, key: str) -> Optional[str]:
        """
        GET команда.

        Args:
            key: Ключ

        Returns:
            Значение или None
        """
        response = self._send_command(f"GET {key}")
        return self._parse_response(response)

    def delete(self, *keys: str) -> int:
        """
        DEL команда.

        Args:
            keys: Ключи для удаления

        Returns:
            Количество удаленных ключей
        """
        cmd = f"DEL {' '.join(keys)}"
        response = self._send_command(cmd)
        return self._parse_response(response)

    def exists(self, *keys: str) -> int:
        """
        EXISTS команда.

        Args:
            keys: Ключи для проверки

        Returns:
            Количество существующих ключей
        """
        cmd = f"EXISTS {' '.join(keys)}"
        response = self._send_command(cmd)
        return self._parse_response(response)

    def ttl(self, key: str) -> int:
        """
        TTL команда.

        Args:
            key: Ключ

        Returns:
            TTL в секундах (-2 если не существует, -1 если бессрочный)
        """
        response = self._send_command(f"TTL {key}")
        return self._parse_response(response)

    def expire(self, key: str, seconds: int) -> bool:
        """
        EXPIRE команда.

        Args:
            key: Ключ
            seconds: TTL в секундах

        Returns:
            True если TTL установлен
        """
        response = self._send_command(f"EXPIRE {key} {seconds}")
        result = self._parse_response(response)
        return bool(result)

    def keys(self, pattern: str = "*") -> List[str]:
        """
        KEYS команда.

        Args:
            pattern: Паттерн поиска

        Returns:
            Список ключей
        """
        response = self._send_command(f"KEYS {pattern}")
        result = self._parse_response(response)
        if isinstance(result, list):
            return result
        return []

    def __enter__(self):
        """Контекстный менеджер."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Контекстный менеджер."""
        self.disconnect()


class RedisError(Exception):
    """Ошибка Redis сервера."""
    pass



if __name__ == "__main__":

    with RedisClient() as client:

        client.set("test_key", "test_value", ex=10)
        print("GET test_key:", client.get("test_key"))

        print("TTL test_key:", client.ttl("test_key"))

        print("EXISTS test_key:", client.exists("test_key"))

        print("KEYS *:", client.keys())

        print("DEL test_key:", client.delete("test_key"))