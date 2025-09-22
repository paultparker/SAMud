"""Main telnet server for SAMud."""

import asyncio
import logging
import signal
import sys

from .commands import CommandHandler
from .database import Database
from .player import PlayerManager
from .world import World

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("samud.log"), logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


class SAMudServer:
    """Main SAMud server."""

    def __init__(self, host: str = "localhost", port: int = 2323):
        self.host = host
        self.port = port
        self.database = Database()
        self.world = World(self.database)
        self.command_handler = CommandHandler(self.world)
        self.player_manager = PlayerManager(self.database, self.world, self.command_handler)
        self.server = None

    async def start(self) -> None:
        """Start the server."""
        logger.info("Initializing SAMud server...")

        # Initialize database
        await self.database.initialize()
        logger.info("Database initialized")

        # Start telnet server
        self.server = await asyncio.start_server(
            self.player_manager.handle_new_connection, self.host, self.port
        )

        addr = self.server.sockets[0].getsockname()
        logger.info(f"SAMud server listening on {addr[0]}:{addr[1]}")
        logger.info("Connect with: telnet localhost 2323")

        # Set up graceful shutdown
        def signal_handler():
            logger.info("Received shutdown signal")
            task = asyncio.create_task(self.stop())
            task.add_done_callback(lambda t: None)

        # Register signal handlers for graceful shutdown
        for sig in (signal.SIGTERM, signal.SIGINT):
            try:
                signal.signal(sig, lambda s, f: signal_handler())
            except ValueError:
                # Signal not supported on this platform
                pass

        # Serve forever
        async with self.server:
            await self.server.serve_forever()

    async def stop(self) -> None:
        """Stop the server gracefully."""
        logger.info("Shutting down SAMud server...")

        if self.server:
            self.server.close()
            await self.server.wait_closed()

        # Close all player connections
        for connection in list(self.player_manager.connections):
            await connection.cleanup()

        logger.info("Server shutdown complete")


async def main() -> None:
    """Main entry point."""
    server = SAMudServer()
    try:
        await server.start()
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received")
    except Exception as e:
        logger.error(f"Server error: {e}")
        raise
    finally:
        await server.stop()


if __name__ == "__main__":
    asyncio.run(main())
