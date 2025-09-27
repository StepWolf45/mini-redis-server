import asyncio
from contextlib import suppress

from src.server.tcp_server import TCPServer


def test_tcp_set_get_and_ttl():
    """Тест базового end-to-end сценария SET/GET/TTL через TCP соединение."""
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


def test_tcp_resp_pipeline_and_keys_patterns():
    """Тест RESP пайплайна и KEYS с шаблонами через TCP."""
    async def scenario():
        server = TCPServer(host="127.0.0.1", port=0)
        task = asyncio.create_task(server.start())

        await asyncio.sleep(0.1)
        port = server.port

        reader, writer = await asyncio.open_connection('127.0.0.1', port)

        # RESP пайплайн: два SET и один GET
        payload = (
            b"*3\r\n$3\r\nSET\r\n$5\r\nuser1\r\n$5\r\nalice\r\n"
            b"*3\r\n$3\r\nSET\r\n$5\r\nuser2\r\n$3\r\nbob\r\n"
            b"*2\r\n$3\r\nGET\r\n$5\r\nuser1\r\n"
        )
        writer.write(payload)
        await writer.drain()

        # Ответы на SET: $2\r\nOK\r\n
        _ = await reader.readline()
        ok1 = await reader.readline()
        _ = await reader.readline()
        ok2 = await reader.readline()
        assert ok1.strip() == b"OK"
        assert ok2.strip() == b"OK"

        # Ответ на GET user1: $5\r\nalice\r\n
        l1 = await reader.readline()
        l2 = await reader.readline()
        assert l1.startswith(b"$")
        assert l2.strip() == b"alice"

        # Проверка KEYS с шаблонами
        writer.write(b"*2\r\n$4\r\nKEYS\r\n$5\r\nuser*\r\n")
        await writer.drain()
        # Ответ: массив из 2 элементов (user1, user2) — порядок не гарантирован, проверяем содержимое
        head = await reader.readline()  # *N\r\n
        assert head.startswith(b"*")
        e1_len = await reader.readline(); e1 = await reader.readline()
        e2_len = await reader.readline(); e2 = await reader.readline()
        s1 = e1.strip().decode(); s2 = e2.strip().decode()
        assert {s1, s2} == {"user1", "user2"}

        writer.close()
        await writer.wait_closed()

        await server.stop()
        task.cancel()
        with suppress(asyncio.CancelledError):
            await task

    asyncio.run(scenario())

def test_tcp_unknown_command_error():
    """Тест обработки неизвестной команды через TCP."""
    async def scenario():
        server = TCPServer(host="127.0.0.1", port=0)
        task = asyncio.create_task(server.start())

        await asyncio.sleep(0.1)
        port = server.port

        reader, writer = await asyncio.open_connection('127.0.0.1', port)
        writer.write(b"PING\r\n")
        await writer.drain()
        err_line = await reader.readline()
        assert err_line.startswith(b"-") # Ожидаем ошибку: неизвестная команда

        writer.close()
        await writer.wait_closed()

        await server.stop()
        task.cancel()
        with suppress(asyncio.CancelledError):
            await task

    asyncio.run(scenario())


def test_tcp_malformed_data():
    """Тест обработки некорректных данных."""
    async def scenario():
        server = TCPServer(host="127.0.0.1", port=0)
        task = asyncio.create_task(server.start())

        await asyncio.sleep(0.1)
        port = server.port

        reader, writer = await asyncio.open_connection('127.0.0.1', port)

        # Отправляем некорректный RESP массив
        writer.write(b"*invalid\r\n")
        await writer.drain()
        err_line = await reader.readline()
        assert err_line.startswith(b"-")  # Ожидаем ошибку протокола

        # Отправляем неполный bulk string
        writer.write(b"$5\r\nhello\r\n")  # Корректный
        await writer.drain()
        _ = await reader.readline()  # Пропускаем ответ

        writer.close()
        await writer.wait_closed()

        await server.stop()
        task.cancel()
        with suppress(asyncio.CancelledError):
            await task

    asyncio.run(scenario())


def test_tcp_timeout_handling():
    """Тест обработки таймаутов чтения."""
    async def scenario():
        server = TCPServer(host="127.0.0.1", port=0)
        task = asyncio.create_task(server.start())

        await asyncio.sleep(0.1)
        port = server.port

        reader, writer = await asyncio.open_connection('127.0.0.1', port)

        # Отправляем неполную команду и ждем таймаут
        writer.write(b"SET key")  # Без \r\n
        await writer.drain()

        await asyncio.sleep(4) 


        try:
            response = await asyncio.wait_for(reader.readline(), timeout=1.0)
            # Если ответ пришел, проверяем ошибку
            assert response.startswith(b"-")
        except asyncio.TimeoutError:
            pass  # Ожидаемо при таймауте

        writer.close()
        await writer.wait_closed()

        await server.stop()
        task.cancel()
        with suppress(asyncio.CancelledError):
            await task

    asyncio.run(scenario())


def test_tcp_incomplete_resp_array():
    """Тест неполного RESP массива."""
    async def scenario():
        server = TCPServer(host="127.0.0.1", port=0)
        task = asyncio.create_task(server.start())

        await asyncio.sleep(0.1)
        port = server.port

        reader, writer = await asyncio.open_connection('127.0.0.1', port)

        # Отправляем неполный RESP массив
        writer.write(b"*2\r\n$3\r\nSET\r\n")
        await writer.drain()

        # Ожидаем ошибку протокола
        response = await reader.readline()
        assert response.startswith(b"-")

        writer.close()
        await writer.wait_closed()

        await server.stop()
        task.cancel()
        with suppress(asyncio.CancelledError):
            await task

    asyncio.run(scenario())


def test_tcp_invalid_resp_array_length():
    """Тест некорректной длины RESP массива."""
    async def scenario():
        server = TCPServer(host="127.0.0.1", port=0)
        task = asyncio.create_task(server.start())

        await asyncio.sleep(0.1)
        port = server.port

        reader, writer = await asyncio.open_connection('127.0.0.1', port)

        # Отправляем массив с некорректной длиной
        writer.write(b"*invalid\r\n")
        await writer.drain()

        response = await reader.readline()
        assert response.startswith(b"-")  # Ошибка протокола

        writer.close()
        await writer.wait_closed()

        await server.stop()
        task.cancel()
        with suppress(asyncio.CancelledError):
            await task

    asyncio.run(scenario())


def test_tcp_invalid_bulk_string():
    """Тест некорректного bulk string в RESP массиве."""
    async def scenario():
        server = TCPServer(host="127.0.0.1", port=0)
        task = asyncio.create_task(server.start())

        await asyncio.sleep(0.1)
        port = server.port

        reader, writer = await asyncio.open_connection('127.0.0.1', port)

        # Массив с некорректным bulk string
        writer.write(b"*1\r\n+notbulk\r\n")
        await writer.drain()

        response = await reader.readline()
        assert response.startswith(b"-") # Ошибка протокола

        writer.close()
        await writer.wait_closed()

        await server.stop()
        task.cancel()
        with suppress(asyncio.CancelledError):
            await task

    asyncio.run(scenario())


def test_tcp_invalid_bulk_length():
    """Тест некорректной длины bulk string."""
    async def scenario():
        server = TCPServer(host="127.0.0.1", port=0)
        task = asyncio.create_task(server.start())

        await asyncio.sleep(0.1)
        port = server.port

        reader, writer = await asyncio.open_connection('127.0.0.1', port)

        # Bulk string с некорректной длиной
        writer.write(b"*1\r\n$invalid\r\n")
        await writer.drain()

        response = await reader.readline()
        assert response.startswith(b"-") 

        writer.close()
        await writer.wait_closed()

        await server.stop()
        task.cancel()
        with suppress(asyncio.CancelledError):
            await task

    asyncio.run(scenario())


def test_tcp_negative_bulk_length():
    """Тест отрицательной длины bulk string."""
    async def scenario():
        server = TCPServer(host="127.0.0.1", port=0)
        task = asyncio.create_task(server.start())

        await asyncio.sleep(0.1)
        port = server.port

        reader, writer = await asyncio.open_connection('127.0.0.1', port)

        # Bulk string с отрицательной длиной
        writer.write(b"*1\r\n$-1\r\n")
        await writer.drain()

        # Должен прочитать следующий bulk string или ошибку
        response = await reader.readline()

        writer.close()
        await writer.wait_closed()

        await server.stop()
        task.cancel()
        with suppress(asyncio.CancelledError):
            await task

    asyncio.run(scenario())


def test_tcp_incomplete_bulk_data():
    """Тест неполных данных bulk string."""
    async def scenario():
        server = TCPServer(host="127.0.0.1", port=0)
        task = asyncio.create_task(server.start())

        await asyncio.sleep(0.1)
        port = server.port

        reader, writer = await asyncio.open_connection('127.0.0.1', port)

        # Bulk string с обещанной длиной, но неполными данными
        writer.write(b"*1\r\n$5\r\nhello\r\n") 
        await writer.drain()
        _ = await reader.readline() 

        # Теперь неполный
        writer.write(b"*1\r\n$5\r\nhi\r\n")  # Длина 5, но только 2 байта + \r\n
        await writer.drain()

        response = await reader.readline()
        assert response.startswith(b"-")  

        writer.close()
        await writer.wait_closed()

        await server.stop()
        task.cancel()
        with suppress(asyncio.CancelledError):
            await task

    asyncio.run(scenario())


def test_tcp_malformed_bulk_termination():
    """Тест некорректного завершения bulk string."""
    async def scenario():
        server = TCPServer(host="127.0.0.1", port=0)
        task = asyncio.create_task(server.start())

        await asyncio.sleep(0.1)
        port = server.port

        reader, writer = await asyncio.open_connection('127.0.0.1', port)

        # Bulk string без \r\n в конце
        writer.write(b"*1\r\n$4\r\ntest\n")
        await writer.drain()

        response = await reader.readline()
        assert response.startswith(b"-")  

        writer.close()
        await writer.wait_closed()

        await server.stop()
        task.cancel()
        with suppress(asyncio.CancelledError):
            await task

    asyncio.run(scenario())

def test_tcp_server_start_stop_exceptions():
    """Тест исключений в start/stop сервера."""
    from unittest.mock import AsyncMock, patch

    async def scenario():
        server = TCPServer(host="127.0.0.1", port=0)

        server._storage.start_cleanup_task = AsyncMock(side_effect=Exception("start error"))
        server._storage.stop_cleanup_task = AsyncMock(side_effect=Exception("stop error"))

        with patch('asyncio.start_server') as mock_start_server:
            from unittest.mock import Mock
            mock_server = AsyncMock()
            mock_socket = Mock()
            mock_socket.getsockname.return_value = ('127.0.0.1', 12345)
            mock_server.sockets = [mock_socket]

            mock_start_server.return_value = mock_server

            # Start должен обработать исключение в cleanup_task
            await server.start()

            # Сервер должен быть запущен несмотря на исключение
            assert server._server is mock_server

            # Stop должен обработать исключение в cleanup_task
            await server.stop()

    asyncio.run(scenario())


def test_tcp_message_size_limits():
    """Тест защиты от слишком больших сообщений."""
    async def scenario():
        server = TCPServer(host="127.0.0.1", port=0)
        task = asyncio.create_task(server.start())

        await asyncio.sleep(0.1)
        port = server.port

        reader, writer = await asyncio.open_connection('127.0.0.1', port)

        # Отправляем слишком большой массив
        large_array = f"*{server.MAX_ARRAY_SIZE + 1}\r\n$1\r\na\r\n".encode()
        writer.write(large_array)
        await writer.drain()

        response = await reader.readline()
        assert response.startswith(b"-")  # Ожидаем ошибку

        # Отправляем bulk string слишком большого размера
        large_bulk = f"$10000001\r\n{'x' * 10000001}\r\n".encode()
        writer.write(large_bulk)
        await writer.drain()

        response = await reader.readline()
        assert response.startswith(b"-")  # Ожидаем ошибку

        writer.close()
        await writer.wait_closed()

        await server.stop()
        task.cancel()
        with suppress(asyncio.CancelledError):
            await task

    asyncio.run(scenario())


def test_tcp_resp_unexpected_types():
    """Тест обработки неожиданных RESP типов на входе."""
    async def scenario():
        server = TCPServer(host="127.0.0.1", port=0)
        task = asyncio.create_task(server.start())

        await asyncio.sleep(0.1)
        port = server.port

        reader, writer = await asyncio.open_connection('127.0.0.1', port)

        # Отправляем simple string 
        writer.write(b"+OK\r\n")
        await writer.drain()

        response = await reader.readline()
        assert response.startswith(b"-")  # Ожидаем ошибку протокола

        # Отправляем integer 
        writer.write(b":42\r\n")
        await writer.drain()

        response = await reader.readline()
        assert response.startswith(b"-")  # Ожидаем ошибку протокола

        # Отправляем error (неожиданно для команд)
        writer.write(b"-ERR test\r\n")
        await writer.drain()

        response = await reader.readline()
        assert response.startswith(b"-")  # Ожидаем ошибку протокола

        writer.close()
        await writer.wait_closed()

        await server.stop()
        task.cancel()
        with suppress(asyncio.CancelledError):
            await task

    asyncio.run(scenario())


