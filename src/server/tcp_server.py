"""
Базовый asyncio TCP сервер.
"""
import asyncio
import logging
from typing import Optional, List
from .command_parser import CommandParser
from .command_handler import CommandHandler
from .storage import Storage


class TCPServer:
    MAX_ARRAY_SIZE = 1000
    MAX_BULK_STRING_SIZE = 1024 * 1024  # 1MB
    MAX_COMMAND_SIZE = 10 * 1024 * 1024  # 10MB
    READ_TIMEOUT = 30.0  

    def __init__(self, host: str = "127.0.0.1", port: int = 0):
        self.host = host
        self.port = port
        self._server: Optional[asyncio.base_events.Server] = None
        self._logger = logging.getLogger(__name__)

        self._storage = Storage()
        self._handler = CommandHandler(self._storage)
        self._parser = CommandParser()

    async def start(self):
        """Запускает TCP сервер и начинает приём клиентских соединений."""
        # запуск фоновой очистки TTL
        try:
            await self._storage.start_cleanup_task()
        except Exception:
            pass
        self._server = await asyncio.start_server(self._handle_client, self.host, self.port, reuse_address=True)
        sock = self._server.sockets[0] if self._server and self._server.sockets else None
        if sock is not None:
            self.port = sock.getsockname()[1]
        self._logger.info(f"TCP server started on {self.host}:{self.port}")

        async with self._server:
            await self._server.serve_forever()

    async def stop(self):
        """Останавливает сервер и корректно закрывает все ресурсы."""
        if self._server is not None:
            self._server.close()
            await self._server.wait_closed()
            self._logger.info("TCP server stopped")
        try:
            await self._storage.stop_cleanup_task()
        except Exception:
            pass

    async def _handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        """
        Обрабатывает подключение клиента: читает строку за строкой и отправляет ответ.

        Args:
            reader: поток чтения для клиента
            writer: поток записи для клиента
        """
        addr = writer.get_extra_info('peername')
        self._logger.debug(f"Client connected: {addr}")
        try:
            while True:
                parts = await self._read_next_command(reader)
                if parts is None:
                    break
                if not parts:
                    continue
                if parts and parts[0] == "-ERR":
                    writer.write(self._parser.format_error(parts[1]).encode('utf-8'))
                    await writer.drain()
                    continue
                name = parts[0]
                args = parts[1:]

                ok, result = self._handler.handle(name, args)
                if ok:
                    resp = self._parser.format_response(result)
                else:
                    resp = self._parser.format_error(result)
                writer.write(resp.encode('utf-8'))
                await writer.drain()
        except asyncio.CancelledError:
            pass
        finally:
            writer.close()
            await writer.wait_closed()
            self._logger.debug(f"Client disconnected: {addr}")

    async def _read_next_command(self, reader: asyncio.StreamReader) -> Optional[List[str]]:
        """
        Читает следующую команду, поддерживая RESP-массивы и inline-формат.
        Возвращает список аргументов или None при закрытии соединения.
        При протокольной ошибке возвращает ["-ERR", message].
        """
        try:
            first = await asyncio.wait_for(reader.readline(), timeout=self.READ_TIMEOUT)
        except asyncio.TimeoutError:
            return ["-ERR", "Protocol error: read timeout"]
        if not first:
            return None

        if len(first) > self.MAX_COMMAND_SIZE:
            return ["-ERR", "Protocol error: command too large"]
        if first.startswith(b"*"):
            # RESP массив
            try:
                count = int(first[1:].strip())
                if count < 0 or count > self.MAX_ARRAY_SIZE:
                    return ["-ERR", "Protocol error: invalid array length"]
            except ValueError:
                return ["-ERR", "Protocol error: invalid array length"]
            items: List[str] = []
            for _ in range(count):
                try:
                    header = await asyncio.wait_for(reader.readline(), timeout=self.READ_TIMEOUT)
                except asyncio.TimeoutError:
                    return ["-ERR", "Protocol error: read timeout"]
                if not header or not header.startswith(b"$"):
                    return ["-ERR", "Protocol error: expected bulk string"]
                try:
                    length = int(header[1:].strip())
                    if length < -1 or length > self.MAX_BULK_STRING_SIZE:
                        return ["-ERR", "Protocol error: invalid bulk length"]
                except ValueError:
                    return ["-ERR", "Protocol error: invalid bulk length"]
                if length < 0:
                    items.append("")
                    continue
                try:
                    data = await asyncio.wait_for(reader.readexactly(length + 2), timeout=self.READ_TIMEOUT)
                except asyncio.IncompleteReadError:
                    return ["-ERR", "Protocol error: unexpected EOF"]
                except asyncio.TimeoutError:
                    return ["-ERR", "Protocol error: read timeout"]
                if not data.endswith(b"\r\n"):
                    return ["-ERR", "Protocol error: bulk not terminated"]
                items.append(data[:-2].decode('utf-8', errors='replace'))
            return items
        elif first.startswith(b"+"):
            return ["-ERR", "Protocol error: unexpected simple string"]
        elif first.startswith(b":"):
            return ["-ERR", "Protocol error: unexpected integer"]
        elif first.startswith(b"-"):
            return ["-ERR", "Protocol error: unexpected error"]
        else:
            # inline команда
            line = first.decode('utf-8', errors='replace').strip()
            return self._parser.parse_command(line)



