"""Tests for world functionality."""

import os
import tempfile

import pytest
from samud.database import Database
from samud.world import World


class MockConnection:
    """Mock connection for testing."""

    def __init__(self, username="testuser"):
        self.username = username
        self.messages = []

    async def send_message(self, message):
        self.messages.append(message)


@pytest.fixture
async def test_world():
    """Create a test world with database."""
    with tempfile.NamedTemporaryFile(delete=False) as f:
        db_path = f.name

    db = Database(db_path)
    await db.initialize()
    world = World(db)

    yield world

    # Cleanup
    if os.path.exists(db_path):
        os.unlink(db_path)


@pytest.mark.asyncio
async def test_room_description(test_world):
    """Test room description generation."""
    description = await test_world.get_room_description(1)
    assert "The Alamo Plaza" in description
    assert "Exits:" in description


@pytest.mark.asyncio
async def test_add_remove_player(test_world):
    """Test adding and removing players from world."""
    conn = MockConnection("testplayer")

    # Add player
    await test_world.add_player(100, conn)
    assert 100 in test_world.active_players

    # Remove player
    await test_world.remove_player(100)
    assert 100 not in test_world.active_players


@pytest.mark.asyncio
async def test_player_movement(test_world):
    """Test player movement between rooms."""
    conn = MockConnection("mover")
    await test_world.add_player(200, conn)

    # Test valid movement
    success, message = await test_world.move_player(200, "east")
    assert success
    assert test_world.active_players[200].current_room_id != 1

    # Test invalid movement
    success, message = await test_world.move_player(200, "up")
    assert not success
    assert "No exit up" in message


@pytest.mark.asyncio
async def test_room_broadcasting(test_world):
    """Test broadcasting messages to room."""
    conn1 = MockConnection("player1")
    conn2 = MockConnection("player2")

    await test_world.add_player(300, conn1)
    await test_world.add_player(301, conn2)

    # Both players start in same room (Alamo Plaza)
    await test_world.broadcast_to_room(1, "Test message")

    # Both should receive the message
    assert len(conn1.messages) > 0
    assert len(conn2.messages) > 0


@pytest.mark.asyncio
async def test_global_broadcasting(test_world):
    """Test broadcasting messages globally."""
    conn1 = MockConnection("global1")
    conn2 = MockConnection("global2")

    await test_world.add_player(400, conn1)
    await test_world.add_player(401, conn2)

    # Move one player to different room
    await test_world.move_player(401, "east")

    # Broadcast globally
    await test_world.broadcast_global("Global test", exclude_user_id=400)

    # Only player2 should receive (player1 excluded)
    assert "Global test" not in str(conn1.messages)
    # Note: conn2 might have other messages from movement


@pytest.mark.asyncio
async def test_online_players(test_world):
    """Test getting online players list."""
    conn1 = MockConnection("online1")
    conn2 = MockConnection("online2")

    await test_world.add_player(500, conn1)
    await test_world.add_player(501, conn2)

    online = test_world.get_online_players()
    assert "online1" in online
    assert "online2" in online
    assert len(online) == 2
