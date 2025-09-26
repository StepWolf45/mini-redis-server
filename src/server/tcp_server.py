"""
Базовый asyncio TCP сервер.
"""
import asyncio
import logging
from typing import Optional


class TCPServer:
    def __init__(self, host: str = "127.0.0.1", port: int = 0):
        self.host = host
        self.port = port
        self._server: Optional[asyncio.base_events.Server] = None
        self._logger = logging.getLogger(__name__)

    async def start(self):
        """Запускает TCP сервер и начинает приём клиентских соединений."""
        self._server = await asyncio.start_server(self._handle_client, self.host, self.port)
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
                data = await reader.readline()
                if not data:
                    break
                line = data.decode('utf-8').strip()
                if not line:
                    continue
                writer.write(b"+OK\r\n")
                await writer.drain()
        except asyncio.CancelledError:
            pass
        finally:
            writer.close()
            await writer.wait_closed()
            self._logger.debug(f"Client disconnected: {addr}")


