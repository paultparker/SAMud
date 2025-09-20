# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a San Antonio-themed Multiuser Dungeon (MUD) project - a text-based multiplayer game accessible via telnet on port 2323. The goal is to create an interactive world featuring San Antonio landmarks like the Alamo, River Walk, and Pearl District where multiple players can explore, chat, and interact.

## Development Commands

This project uses **uv** for Python package management. Common development commands:

### Setup
```bash
make init              # Create venv, sync deps, install pre-commit hook
uv sync --all-groups   # Install all dependencies
```

### Development Workflow
```bash
make check             # Run all checks: format + lint + type + test
make fmt               # Format code with ruff
make lint              # Lint with ruff check
make type              # Type-check with mypy
make test              # Run pytest
make cov               # Run pytest with coverage
```

### Package Management
```bash
make add name=PKG      # Add runtime dependency
make dev name=PKG      # Add dev dependency
```

### Other Commands
```bash
make run               # Run as module: python -m samud
make build             # Build wheel/sdist
make clean             # Remove caches and build artifacts
```

## Project Structure

- Package name: `samud` (San Antonio MUD)
- Uses Python 3.11+ with modern tooling (ruff, mypy, pytest)
- Configured for strict type checking and code formatting
- Hardcoded configuration: port 2323, SQLite database at `samud.db`

## Key Requirements to Implement

### Core Features
- Telnet server on port 2323
- User authentication (signup/login)
- SQLite database for player state persistence
- Room-based world with 7 San Antonio landmarks:
  - The Alamo Plaza (starting location)
  - River Walk North
  - River Walk South
  - The Pearl
  - Tower of the Americas
  - Mission San José
  - Southtown

### Essential Commands
- `look` - room description, exits, players
- `say <message>` - room chat
- `shout <message>` - global chat
- Movement commands (`move <exit>`, `n`, `s`, `e`, `w`)
- `who` - online players
- `where` - current location
- `help` - command list
- `quit` - save and disconnect

### Architecture Considerations
- Async/await for handling multiple concurrent telnet connections
- Separate modules for: networking, world/rooms, player management, commands, database
- Simple message broadcasting system by iterating connected players
- Clean separation between game logic and network handling

## Tool Configuration

- **Ruff**: Line length 100, Python 3.11 target, strict linting rules
- **MyPy**: Strict type checking enabled
- **Pytest**: Configured for quiet output, tests in `tests/` directory
- **Coverage**: Branch coverage tracking, source in `src/`