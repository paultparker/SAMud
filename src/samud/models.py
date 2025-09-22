"""Data models for SAMud."""

from dataclasses import dataclass
from datetime import datetime


@dataclass
class User:
    """User account model."""

    id: int
    username: str
    password_hash: str
    created_at: datetime
    updated_at: datetime


@dataclass
class Room:
    """Room model."""

    id: int
    name: str
    description: str


@dataclass
class Exit:
    """Room exit model."""

    id: int
    from_room_id: int
    to_room_id: int
    direction: str


@dataclass
class Player:
    """Active player state."""

    id: int
    user_id: int
    current_room_id: int
    last_seen_at: datetime
    connection: object | None = None  # Will be the telnet connection
