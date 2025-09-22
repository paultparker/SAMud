"""World and room management for SAMud."""

from .database import Database
from .models import Player


class World:
    """Manages the game world state."""

    def __init__(self, database: Database):
        self.database = database
        self.active_players: dict[int, Player] = {}  # user_id -> Player

    async def get_room_description(self, room_id: int) -> str:
        """Get formatted room description with exits and players."""
        room = await self.database.get_room(room_id)
        if not room:
            return "You are in a void. This shouldn't happen!"

        # Get exits
        exits = await self.database.get_room_exits(room_id)
        exit_directions = [exit.direction for exit in exits]

        # Get players in room
        players_here = [
            player.connection.username
            for player in self.active_players.values()
            if player.current_room_id == room_id and hasattr(player.connection, "username")
        ]

        # Format description
        description = f"{room.name}\n{room.description}\n"

        if exit_directions:
            description += f"Exits: {', '.join(sorted(exit_directions))}\n"

        if players_here:
            description += f"Players here: {', '.join(players_here)}\n"

        return description

    async def move_player(self, user_id: int, direction: str) -> tuple[bool, str]:
        """Move player in given direction. Returns (success, message)."""
        if user_id not in self.active_players:
            return False, "You are not in the world."

        player = self.active_players[user_id]
        current_room = player.current_room_id

        # Find exit in that direction
        exits = await self.database.get_room_exits(current_room)
        target_exit = None
        for exit in exits:
            if exit.direction.lower() == direction.lower():
                target_exit = exit
                break

        if not target_exit:
            return False, f"No exit {direction}."

        # Move player
        old_room_id = player.current_room_id
        player.current_room_id = target_exit.to_room_id
        await self.database.save_player_location(user_id, target_exit.to_room_id)

        # Get new room info
        new_room = await self.database.get_room(target_exit.to_room_id)
        if not new_room:
            return False, "Cannot move to that location."

        # Notify other players in old room
        old_room_message = f"{player.connection.username} leaves {direction}."
        await self.broadcast_to_room(old_room_id, old_room_message, exclude_user_id=user_id)

        # Notify other players in new room
        new_room_message = f"{player.connection.username} arrives."
        await self.broadcast_to_room(
            target_exit.to_room_id, new_room_message, exclude_user_id=user_id
        )

        return True, await self.get_room_description(target_exit.to_room_id)

    async def add_player(self, user_id: int, connection: object) -> None:
        """Add player to the world."""
        room_id = await self.database.get_player_location(user_id)

        player = Player(
            id=user_id,
            user_id=user_id,
            current_room_id=room_id,
            last_seen_at=None,  # Will be set by database
            connection=connection,
        )

        self.active_players[user_id] = player

        # Notify other players in the room
        if hasattr(connection, "username"):
            message = f"{connection.username} appears."
            await self.broadcast_to_room(room_id, message, exclude_user_id=user_id)

    async def remove_player(self, user_id: int) -> None:
        """Remove player from the world."""
        if user_id in self.active_players:
            player = self.active_players[user_id]

            # Notify other players
            if hasattr(player.connection, "username"):
                message = f"{player.connection.username} disappears."
                await self.broadcast_to_room(
                    player.current_room_id, message, exclude_user_id=user_id
                )

            # Save final location
            await self.database.save_player_location(user_id, player.current_room_id)
            del self.active_players[user_id]

    async def broadcast_to_room(
        self, room_id: int, message: str, exclude_user_id: int | None = None
    ) -> None:
        """Send message to all players in a room."""
        for user_id, player in self.active_players.items():
            if player.current_room_id == room_id and user_id != exclude_user_id:
                if hasattr(player.connection, "send_message"):
                    await player.connection.send_message(message)

    async def broadcast_global(self, message: str, exclude_user_id: int | None = None) -> None:
        """Send message to all connected players."""
        for user_id, player in self.active_players.items():
            if user_id != exclude_user_id:
                if hasattr(player.connection, "send_message"):
                    await player.connection.send_message(message)

    def get_online_players(self) -> list[str]:
        """Get list of online player names."""
        return [
            player.connection.username
            for player in self.active_players.values()
            if hasattr(player.connection, "username")
        ]

    def get_player_room_name(self, user_id: int) -> str | None:
        """Get the name of the room a player is in."""
        if user_id in self.active_players:
            room_id = self.active_players[user_id].current_room_id
            # We'll need to cache room names or make this async
            return f"Room {room_id}"  # Simplified for now
        return None
