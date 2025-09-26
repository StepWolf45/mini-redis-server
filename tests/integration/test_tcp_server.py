import asyncio
from contextlib import suppress

from src.server.tcp_server import TCPServer


def test_tcp_server_basic_ok_response():
    async def scenario():
        server = TCPServer(host="127.0.0.1", port=0)
        task = asyncio.create_task(server.start())
        # дать серверу подняться и назначить порт
        await asyncio.sleep(0.1)
        port = server.port

        reader, writer = await asyncio.open_connection('127.0.0.1', port)
        writer.write(b"PING\r\n")
        await writer.drain()
        data = await reader.readline()
        assert data == b"+OK\r\n"

        writer.close()
        await writer.wait_closed()

        await server.stop()
        task.cancel()
        with suppress(asyncio.CancelledError):
            await task

    asyncio.run(scenario())


