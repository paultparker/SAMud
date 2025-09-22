"""Database operations for SAMud."""

from datetime import datetime

import aiosqlite
import bcrypt

from .models import Exit, Room, User


class Database:
    """Handles all database operations."""

    def __init__(self, db_path: str = "samud.db"):
        self.db_path = db_path

    async def initialize(self) -> None:
        """Initialize database with schema and seed data."""
        async with aiosqlite.connect(self.db_path) as db:
            await self._create_tables(db)
            await self._seed_rooms(db)
            await db.commit()

    async def _create_tables(self, db: aiosqlite.Connection) -> None:
        """Create database tables."""
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS rooms (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT NOT NULL
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS exits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                from_room_id INTEGER NOT NULL,
                to_room_id INTEGER NOT NULL,
                direction TEXT NOT NULL,
                FOREIGN KEY (from_room_id) REFERENCES rooms (id),
                FOREIGN KEY (to_room_id) REFERENCES rooms (id)
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS players (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                current_room_id INTEGER NOT NULL,
                last_seen_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (current_room_id) REFERENCES rooms (id)
            )
        """)

    async def _seed_rooms(self, db: aiosqlite.Connection) -> None:
        """Seed the database with San Antonio landmark rooms."""
        # Check if rooms already exist
        async with db.execute("SELECT COUNT(*) FROM rooms") as cursor:
            count = await cursor.fetchone()
            if count[0] > 0:
                return

        # Insert the 7 San Antonio landmark rooms
        rooms = [
            (
                1,
                "The Alamo Plaza",
                "You stand in the historic Alamo Plaza, where Texas heroes made their last stand. "
                "The limestone walls of the chapel rise before you.",
            ),
            (
                2,
                "River Walk North",
                "The San Antonio River flows gently beside the stone walkway. "
                "Cypress trees provide shade while colorful umbrellas mark restaurant patios.",
            ),
            (
                3,
                "River Walk South",
                "Here the River Walk takes on a quieter character. "
                "Native plants line the banks and you can hear the gentle splash of water.",
            ),
            (
                4,
                "The Pearl",
                "This trendy district buzzes with activity. "
                "The converted brewery buildings house upscale shops and restaurants.",
            ),
            (
                5,
                "Tower of the Americas",
                "The 750-foot tower stretches skyward, a remnant of the 1968 World's Fair. "
                "From here you can see across all of San Antonio's sprawling landscape.",
            ),
            (
                6,
                "Mission San José",
                "The 'Queen of Missions' stands in quiet dignity. "
                "The carved rose window catches the Texas sun.",
            ),
            (
                7,
                "Southtown",
                "This eclectic neighborhood pulses with local art and culture. "
                "Colorful murals cover building walls while food trucks serve authentic flavors.",
            ),
        ]

        for room_id, name, description in rooms:
            await db.execute(
                "INSERT INTO rooms (id, name, description) VALUES (?, ?, ?)",
                (room_id, name, description),
            )

        # Create exits between rooms (forming a connected world)
        exits = [
            (1, 2, "east"),  # Alamo Plaza -> River Walk North
            (2, 1, "west"),  # River Walk North -> Alamo Plaza
            (2, 3, "south"),  # River Walk North -> River Walk South
            (3, 2, "north"),  # River Walk South -> River Walk North
            (3, 4, "east"),  # River Walk South -> The Pearl
            (4, 3, "west"),  # The Pearl -> River Walk South
            (1, 5, "south"),  # Alamo Plaza -> Tower of the Americas
            (5, 1, "north"),  # Tower of the Americas -> Alamo Plaza
            (5, 6, "south"),  # Tower of the Americas -> Mission San José
            (6, 5, "north"),  # Mission San José -> Tower of the Americas
            (6, 7, "west"),  # Mission San José -> Southtown
            (7, 6, "east"),  # Southtown -> Mission San José
            (7, 3, "north"),  # Southtown -> River Walk South
            (3, 7, "south"),  # River Walk South -> Southtown
        ]

        for from_room, to_room, direction in exits:
            await db.execute(
                "INSERT INTO exits (from_room_id, to_room_id, direction) VALUES (?, ?, ?)",
                (from_room, to_room, direction),
            )

    async def create_user(self, username: str, password: str) -> User | None:
        """Create a new user account."""
        password_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
        now = datetime.utcnow().isoformat()

        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute(
                    "INSERT INTO users (username, password_hash, created_at, updated_at) "
                    "VALUES (?, ?, ?, ?)",
                    (username, password_hash, now, now),
                )
                user_id = cursor.lastrowid
                await db.commit()

                return User(
                    id=user_id,
                    username=username,
                    password_hash=password_hash,
                    created_at=datetime.fromisoformat(now),
                    updated_at=datetime.fromisoformat(now),
                )
        except aiosqlite.IntegrityError:
            return None  # Username already exists

    async def authenticate_user(self, username: str, password: str) -> User | None:
        """Authenticate a user login."""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT id, username, password_hash, created_at, updated_at "
                "FROM users WHERE username = ?",
                (username,),
            ) as cursor:
                row = await cursor.fetchone()
                if not row:
                    return None

                if bcrypt.checkpw(password.encode("utf-8"), row[2].encode("utf-8")):
                    return User(
                        id=row[0],
                        username=row[1],
                        password_hash=row[2],
                        created_at=datetime.fromisoformat(row[3]),
                        updated_at=datetime.fromisoformat(row[4]),
                    )
                return None

    async def get_room(self, room_id: int) -> Room | None:
        """Get room by ID."""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT id, name, description FROM rooms WHERE id = ?", (room_id,)
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    return Room(id=row[0], name=row[1], description=row[2])
                return None

    async def get_room_exits(self, room_id: int) -> list[Exit]:
        """Get all exits from a room."""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT id, from_room_id, to_room_id, direction FROM exits WHERE from_room_id = ?",
                (room_id,),
            ) as cursor:
                rows = await cursor.fetchall()
                return [
                    Exit(id=row[0], from_room_id=row[1], to_room_id=row[2], direction=row[3])
                    for row in rows
                ]

    async def save_player_location(self, user_id: int, room_id: int) -> None:
        """Save or update player's current location."""
        now = datetime.utcnow().isoformat()

        async with aiosqlite.connect(self.db_path) as db:
            # Check if player record exists
            async with db.execute("SELECT id FROM players WHERE user_id = ?", (user_id,)) as cursor:
                existing = await cursor.fetchone()

            if existing:
                await db.execute(
                    "UPDATE players SET current_room_id = ?, last_seen_at = ? WHERE user_id = ?",
                    (room_id, now, user_id),
                )
            else:
                await db.execute(
                    "INSERT INTO players (user_id, current_room_id, last_seen_at) VALUES (?, ?, ?)",
                    (user_id, room_id, now),
                )
            await db.commit()

    async def get_player_location(self, user_id: int) -> int:
        """Get player's last known location, defaults to Alamo Plaza (room 1)."""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT current_room_id FROM players WHERE user_id = ?", (user_id,)
            ) as cursor:
                row = await cursor.fetchone()
                return row[0] if row else 1  # Default to Alamo Plaza
