"""Tests for database functionality."""

import os
import tempfile

import pytest
from samud.database import Database


@pytest.fixture
async def test_db():
    """Create a temporary test database."""
    with tempfile.NamedTemporaryFile(delete=False) as f:
        db_path = f.name

    db = Database(db_path)
    await db.initialize()
    yield db

    # Cleanup
    if os.path.exists(db_path):
        os.unlink(db_path)


@pytest.mark.asyncio
async def test_database_initialization(test_db):
    """Test database initialization creates tables and rooms."""
    # Check that rooms were created
    room = await test_db.get_room(1)
    assert room is not None
    assert room.name == "The Alamo Plaza"

    # Check that exits were created
    exits = await test_db.get_room_exits(1)
    assert len(exits) > 0


@pytest.mark.asyncio
async def test_user_creation(test_db):
    """Test user creation and authentication."""
    # Create user
    user = await test_db.create_user("testuser", "password123")
    assert user is not None
    assert user.username == "testuser"
    assert user.id > 0

    # Test duplicate username
    duplicate = await test_db.create_user("testuser", "different")
    assert duplicate is None


@pytest.mark.asyncio
async def test_user_authentication(test_db):
    """Test user authentication."""
    # Create user
    await test_db.create_user("authtest", "secret")

    # Test valid login
    user = await test_db.authenticate_user("authtest", "secret")
    assert user is not None
    assert user.username == "authtest"

    # Test invalid password
    invalid = await test_db.authenticate_user("authtest", "wrong")
    assert invalid is None

    # Test non-existent user
    missing = await test_db.authenticate_user("nobody", "password")
    assert missing is None


@pytest.mark.asyncio
async def test_player_location(test_db):
    """Test player location saving and retrieval."""
    # Create user
    user = await test_db.create_user("loctest", "password")

    # Test default location (should be Alamo Plaza)
    location = await test_db.get_player_location(user.id)
    assert location == 1

    # Save new location
    await test_db.save_player_location(user.id, 3)
    location = await test_db.get_player_location(user.id)
    assert location == 3


@pytest.mark.asyncio
async def test_room_retrieval(test_db):
    """Test room data retrieval."""
    # Test valid room
    room = await test_db.get_room(2)
    assert room is not None
    assert "River Walk North" in room.name

    # Test invalid room
    invalid_room = await test_db.get_room(999)
    assert invalid_room is None


@pytest.mark.asyncio
async def test_room_exits(test_db):
    """Test room exit retrieval."""
    exits = await test_db.get_room_exits(1)  # Alamo Plaza
    assert len(exits) > 0

    # Check that exits have proper structure
    exit_directions = [exit.direction for exit in exits]
    assert "east" in exit_directions or "south" in exit_directions
