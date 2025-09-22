"""Command handlers for SAMud."""

from collections.abc import Callable

from .world import World


class CommandHandler:
    """Handles parsing and executing player commands."""

    def __init__(self, world: World):
        self.world = world
        self.commands: dict[str, Callable] = {
            "help": self.cmd_help,
            "look": self.cmd_look,
            "say": self.cmd_say,
            "shout": self.cmd_shout,
            "move": self.cmd_move,
            "n": lambda conn, args: self.cmd_move(conn, ["north"]),
            "s": lambda conn, args: self.cmd_move(conn, ["south"]),
            "e": lambda conn, args: self.cmd_move(conn, ["east"]),
            "w": lambda conn, args: self.cmd_move(conn, ["west"]),
            "north": lambda conn, args: self.cmd_move(conn, ["north"]),
            "south": lambda conn, args: self.cmd_move(conn, ["south"]),
            "east": lambda conn, args: self.cmd_move(conn, ["east"]),
            "west": lambda conn, args: self.cmd_move(conn, ["west"]),
            "who": self.cmd_who,
            "where": self.cmd_where,
            "quit": self.cmd_quit,
        }

    async def handle_command(self, connection: object, command_line: str) -> bool:
        """Parse and execute a command. Returns True if connection should continue."""
        command_line = command_line.strip()
        if not command_line:
            return True

        parts = command_line.split()
        command = parts[0].lower()
        args = parts[1:]

        if command in self.commands:
            try:
                result = await self.commands[command](connection, args)
                # If quit command returns False, signal to close connection
                if command == "quit" and result is False:
                    return False
            except Exception as e:
                await connection.send_message(f"Error executing command: {e}")
        else:
            await connection.send_message("Unknown command. Type 'help' for available commands.")

        return True

    async def cmd_help(self, connection: object, args: list) -> None:
        """Show available commands."""
        help_text = """
Available commands:
  look              - Show room description, exits, and players
  say <message>     - Talk to players in your current room
  shout <message>   - Send message to all players globally
  move <direction>  - Move in a direction (n/s/e/w)
  n, s, e, w        - Short movement commands
  who               - List all online players
  where             - Show your current location
  help              - Show this help message
  quit              - Save and disconnect

Welcome to San Antonio! Start at The Alamo Plaza and explore the city.
        """.strip()
        await connection.send_message(help_text)

    async def cmd_look(self, connection: object, args: list) -> None:
        """Show current room description."""
        user_id = getattr(connection, "user_id", None)
        if user_id and user_id in self.world.active_players:
            player = self.world.active_players[user_id]
            description = await self.world.get_room_description(player.current_room_id)
            await connection.send_message(description)
        else:
            await connection.send_message("You are not in the world.")

    async def cmd_say(self, connection: object, args: list) -> None:
        """Say something to players in the current room."""
        if not args:
            await connection.send_message("Say what?")
            return

        message = " ".join(args)
        username = getattr(connection, "username", "Someone")
        user_id = getattr(connection, "user_id", None)

        if user_id and user_id in self.world.active_players:
            player = self.world.active_players[user_id]
            room_message = f"[Room] {username}: {message}"

            # Send to sender
            await connection.send_message(f"[Room] you: {message}")

            # Send to others in room
            await self.world.broadcast_to_room(
                player.current_room_id, room_message, exclude_user_id=user_id
            )
        else:
            await connection.send_message("You are not in the world.")

    async def cmd_shout(self, connection: object, args: list) -> None:
        """Shout a message to all players."""
        if not args:
            await connection.send_message("Shout what?")
            return

        message = " ".join(args)
        username = getattr(connection, "username", "Someone")
        user_id = getattr(connection, "user_id", None)

        # Send to sender
        await connection.send_message(f"[Global] you: {message}")

        # Send to everyone else
        global_message = f"[Global] {username}: {message}"
        await self.world.broadcast_global(global_message, exclude_user_id=user_id)

    async def cmd_move(self, connection: object, args: list) -> None:
        """Move in a direction."""
        if not args:
            await connection.send_message("Move which direction?")
            return

        direction = args[0].lower()
        user_id = getattr(connection, "user_id", None)

        if user_id:
            _success, message = await self.world.move_player(user_id, direction)
            await connection.send_message(message)
        else:
            await connection.send_message("You are not in the world.")

    async def cmd_who(self, connection: object, args: list) -> None:
        """List online players."""
        online_players = self.world.get_online_players()
        if online_players:
            player_list = "\n".join(f"  {name}" for name in sorted(online_players))
            message = f"Online players:\n{player_list}"
        else:
            message = "No players are currently online."
        await connection.send_message(message)

    async def cmd_where(self, connection: object, args: list) -> None:
        """Show current location."""
        user_id = getattr(connection, "user_id", None)
        if user_id and user_id in self.world.active_players:
            player = self.world.active_players[user_id]
            room = await self.world.database.get_room(player.current_room_id)
            if room:
                await connection.send_message(f"You are in: {room.name}")
            else:
                await connection.send_message("You are in an unknown location.")
        else:
            await connection.send_message("You are not in the world.")

    async def cmd_quit(self, connection: object, args: list) -> bool:
        """Quit the game."""
        user_id = getattr(connection, "user_id", None)
        if user_id:
            await self.world.remove_player(user_id)

        await connection.send_message("Goodbye! Your progress has been saved.")
        return False  # Signal to close connection
