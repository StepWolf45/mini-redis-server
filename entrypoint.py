
"""
Entrypoint script for running the mini Redis server.
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from server.tcp_server import TCPServer


async def main():
    """Main entrypoint function."""
    
    host = os.getenv('REDIS_HOST', '0.0.0.0')  # Слушаем все интерфейсы в докере
    port = int(os.getenv('REDIS_PORT', '6379'))  # Стандартный Redis порт

    server = TCPServer(host=host, port=port)

    try:
        await server.start()
    except KeyboardInterrupt:
        print("Server interrupted by user")
    except Exception as e:
        print(f"Server error: {e}")
        sys.exit(1)
    finally:
        await server.stop()


if __name__ == "__main__":
    asyncio.run(main())