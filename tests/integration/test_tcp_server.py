import asyncio
from contextlib import suppress

from src.server.tcp_server import TCPServer


def test_tcp_set_get_and_ttl():
    async def scenario():
        server = TCPServer(host="127.0.0.1", port=0)
        task = asyncio.create_task(server.start())
        await asyncio.sleep(0.1)
        port = server.port
        reader, writer = await asyncio.open_connection('127.0.0.1', port)

        # SET a 1: устанавливаем значение ключа
        writer.write(b"SET a 1\r\n")
        await writer.drain()
        # RESP bulk string: первая строка — длина, вторая — само значение
        line1 = await reader.readline()  # $2\r\n
        line2 = await reader.readline()  # OK\r\n
        assert line1.startswith(b"$")
        assert line2.strip() == b"OK"

        # GET a: читаем значение ключа
        writer.write(b"GET a\r\n")
        await writer.drain()
        line1 = await reader.readline()  # $1\r\n
        line2 = await reader.readline()  # 1\r\n
        assert line1.startswith(b"$")
        assert line2.strip() == b"1"
            
        # SET b EX 1 — устанавливаем TTL в 1 секунду
        writer.write(b"SET b v EX 1\r\n")
        await writer.drain()
        _ = await reader.readline()  # $2\r\n
        ok_line = await reader.readline()  # OK\r\n
        assert ok_line.strip() == b"OK"

        # TTL b — TTL должен быть >= 0
        writer.write(b"TTL b\r\n")
        await writer.drain()
        ttl_line = await reader.readline()  # :<n>\r\n
        assert ttl_line.startswith(b":")

        # Ждём истечения TTL
        await asyncio.sleep(1.1)
        writer.write(b"GET b\r\n")
        await writer.drain()
        null_line = await reader.readline()  # $-1\r\n
        assert null_line.strip() == b"$-1"

        writer.close()
        await writer.wait_closed()

        await server.stop()
        task.cancel()
        with suppress(asyncio.CancelledError):
            await task

    asyncio.run(scenario())


def test_tcp_unknown_command_error():
    async def scenario():
        server = TCPServer(host="127.0.0.1", port=0)
        task = asyncio.create_task(server.start())

        await asyncio.sleep(0.1)
        port = server.port

        reader, writer = await asyncio.open_connection('127.0.0.1', port)
        writer.write(b"PING\r\n")
        await writer.drain()
        err_line = await reader.readline()
        # ожидаем ошибку: неизвестная команда
        assert err_line.startswith(b"-")  

        writer.close()
        await writer.wait_closed()

        await server.stop()
        task.cancel()
        with suppress(asyncio.CancelledError):
            await task

    asyncio.run(scenario())


