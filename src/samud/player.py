"""Player connection management for SAMud."""

import asyncio
import logging

from .commands import CommandHandler
from .database import Database
from .models import User
from .world import World

logger = logging.getLogger(__name__)


class PlayerConnection:
    """Manages a single player's telnet connection."""

    def __init__(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
        database: Database,
        world: World,
        command_handler: CommandHandler,
    ):
        self.reader = reader
        self.writer = writer
        self.database = database
        self.world = world
        self.command_handler = command_handler
        self.user: User | None = None
        self.username: str | None = None
        self.user_id: int | None = None
        self.authenticated = False

    async def send_message(self, message: str) -> None:
        """Send a message to the client."""
        try:
            self.writer.write(f"{message}\r\n".encode())
            await self.writer.drain()
        except Exception as e:
            logger.error(f"Failed to send message to {self.username}: {e}")

    async def send_prompt(self, prompt: str = "> ") -> None:
        """Send a prompt without newline."""
        try:
            self.writer.write(prompt.encode("utf-8"))
            await self.writer.drain()
        except Exception as e:
            logger.error(f"Failed to send prompt to {self.username}: {e}")

    async def read_line(self) -> str | None:
        """Read a line from the client."""
        try:
            data = await self.reader.readline()
            if not data:
                return None
            return data.decode("utf-8").strip()
        except Exception as e:
            logger.error(f"Failed to read from {self.username}: {e}")
            return None

    async def handle_connection(self) -> None:
        """Main connection handler."""
        client_addr = self.writer.get_extra_info("peername")
        logger.info(f"New connection from {client_addr}")

        try:
            await self.send_welcome()

            # Authentication loop
            while not self.authenticated:
                success = await self.handle_authentication()
                if not success:
                    return

            # Add player to world
            await self.world.add_player(self.user_id, self)
            logger.info(f"Player {self.username} logged in")

            # Show initial room
            await self.command_handler.cmd_look(self, [])

            # Main game loop
            while True:
                await self.send_prompt()
                command = await self.read_line()

                if command is None:  # Connection closed
                    break

                # Handle command
                continue_session = await self.command_handler.handle_command(self, command)
                if not continue_session:
                    break

        except Exception as e:
            logger.error(f"Error in connection handler for {self.username}: {e}")
        finally:
            await self.cleanup()

    async def send_welcome(self) -> None:
        """Send welcome banner."""
        banner = """
╔══════════════════════════════════════════════════════════════╗
║                    Welcome to SAMud                          ║
║              San Antonio Multi-User Dungeon                  ║
║                                                              ║
║    Explore the Alamo City's landmarks and chat with         ║
║    fellow adventurers in this text-based adventure!         ║
║                                                              ║
║    Type 'login' or 'signup' to begin                        ║
╚══════════════════════════════════════════════════════════════╝
        """.strip()
        await self.send_message(banner)

    async def handle_authentication(self) -> bool:
        """Handle login/signup process. Returns True if successful."""
        await self.send_prompt("login or signup: ")
        choice = await self.read_line()

        if choice is None:
            return False

        choice = choice.lower().strip()

        if choice == "login":
            return await self.handle_login()
        elif choice == "signup":
            return await self.handle_signup()
        else:
            await self.send_message("Please type 'login' or 'signup'")
            return True  # Continue authentication loop

    async def handle_login(self) -> bool:
        """Handle user login."""
        await self.send_prompt("Username: ")
        username = await self.read_line()
        if not username:
            return False

        await self.send_prompt("Password: ")
        password = await self.read_line()
        if not password:
            return False

        user = await self.database.authenticate_user(username, password)
        if user:
            self.user = user
            self.username = user.username
            self.user_id = user.id
            self.authenticated = True
            await self.send_message(f"Welcome back, {username}!")
            return True
        else:
            await self.send_message("Invalid username or password.")
            return True  # Continue authentication loop

    async def handle_signup(self) -> bool:
        """Handle user signup."""
        await self.send_prompt("Choose username: ")
        username = await self.read_line()
        if not username:
            return False

        # Basic username validation
        if len(username) < 3 or len(username) > 20:
            await self.send_message("Username must be 3-20 characters long.")
            return True

        if not username.isalnum():
            await self.send_message("Username must contain only letters and numbers.")
            return True

        await self.send_prompt("Choose password: ")
        password = await self.read_line()
        if not password:
            return False

        # No password complexity requirements as per PRD
        if len(password) < 1:
            await self.send_message("Password cannot be empty.")
            return True

        user = await self.database.create_user(username, password)
        if user:
            self.user = user
            self.username = user.username
            self.user_id = user.id
            self.authenticated = True
            await self.send_message(f"Account created! Welcome to San Antonio, {username}!")
            await self.send_message("You appear at The Alamo Plaza...")
            return True
        else:
            await self.send_message("Username already exists. Please choose another.")
            return True  # Continue authentication loop

    async def cleanup(self) -> None:
        """Clean up connection resources."""
        if self.user_id:
            await self.world.remove_player(self.user_id)
            logger.info(f"Player {self.username} disconnected")

        try:
            self.writer.close()
            await self.writer.wait_closed()
        except Exception as e:
            logger.error(f"Error closing connection for {self.username}: {e}")


class PlayerManager:
    """Manages all player connections."""

    def __init__(self, database: Database, world: World, command_handler: CommandHandler):
        self.database = database
        self.world = world
        self.command_handler = command_handler
        self.connections = set()

    async def handle_new_connection(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ) -> None:
        """Handle a new telnet connection."""
        connection = PlayerConnection(
            reader, writer, self.database, self.world, self.command_handler
        )
        self.connections.add(connection)

        try:
            await connection.handle_connection()
        finally:
            self.connections.discard(connection)
