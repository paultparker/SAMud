# SAMud — Product Requirements Document (PRD)

## 1) Summary
SAMud is a lightweight, San Antonio–themed multi‑user dungeon (MUD) that runs as a telnet‑accessible server. MVP focuses on real‑time multi‑user room navigation, in‑room and global chat, basic persistence of player state (username, credential, last room), and a minimum set of rooms modeled after iconic San Antonio landmarks.

## 2) Goals & Non‑Goals
**Goals**
- Provide a simple, hackable MUD that people can connect to using telnet on port 2323.
- Deliver a cohesive “sense of place” via at least six San Antonio landmarks with short descriptions and inter‑room exits.
- Support simultaneous users who can see each other and communicate via room and global chat.
- Persist player state in a local SQLite database (MVP).

**Non‑Goals (MVP)**
- Rich graphics/UI beyond telnet.
- Complex combat/economy/quest systems.
- Account recovery, email, OAuth, or web front‑end.
- Horizontal scaling across multiple servers.

## 2a) Confirmed Decisions
- **Language/Runtime**: Python
- **Password complexity**: none required (still hash + salt)
- **Locations**: no additional locations beyond the core set (see World Model)

## 3) Users & Use Cases
**Primary users**
- Casual players: discover the world, chat, and wander between rooms.
- Event participants / learners: connect during a workshop or meetup to observe multi‑user state and messaging.

**Representative use cases**
- Join the server, sign up, appear at The Alamo Plaza, chat with others, move to River Walk, and disconnect; resume later at last room.
- Two users in the same room use `say` to talk; one uses `shout` to broadcast globally; both use `who` to see who’s online.

## 4) Functional Requirements (MVP)
### 4.1 Connectivity & Protocol
- Server accepts telnet TCP connections on **port 2323**.
- Multiple simultaneous connections supported.

### 4.2 Account & Session
- **Signup**: username uniqueness enforced; password set on creation.
- **Login**: authenticate returning players.
- **Quit**: saves player state (at minimum: last room) and cleanly disconnects.

### 4.3 World Model
- Provide **exactly the following six rooms** themed to San Antonio: The Alamo Plaza; River Walk North; River Walk South; The Pearl; Tower of the Americas; Mission San José; Southtown. (No additional locations in MVP.)
- Each room has: id/name, short description, exits (n/s/e/w or named), and list of present players.
- Movement: `move <exit>` or `n|s|e|w` shorthands change rooms if an exit exists; movement updates room rosters and notifies affected rooms if needed.

### 4.4 Chat & Presence
- **Room chat**: `say <message>` visible to players in the same room (prefix clearly with speaker and scope).
- **Global chat**: `shout <message>` broadcast to all connected players.
- **Presence**: `who` lists online players; `where` shows your current room.
- **Help**: `help` lists available commands and syntax.

### 4.5 Persistence
- SQLite DB stores users (username, **salted password hash**; no minimum password complexity requirement) and last room; optional timestamps and audit fields.

### 4.6 CLI/UX
- On connect: welcome banner and prompt to `login` or `signup`.
- After login/signup: render current room description, exits, and players present.
- Standard prompts, input echo, and error messages (“Unknown command”, “No exit east”, etc.).

## 5) Non‑Functional Requirements
- **Simplicity**: runnable locally with minimal dependencies.
- **Stability**: gracefully handle disconnects; no server crash on malformed input.
- **Performance**: support ~20 concurrent players on a typical laptop without perceptible lag.
- **Security (MVP)**: salted password hashing; no plaintext storage; **no minimum password complexity requirement**. No network encryption required for MVP (telnet in trusted/demo contexts); document risks.
- **Observability**: basic structured logging for connects, disconnects, logins, movement, chat, and errors.

## 6) Command Reference (MVP)
- `look` — show room description, exits, players present.
- `say <message>` — room‑scoped chat.
- `shout <message>` — global broadcast.
- `move <exit>` or `n|s|e|w` — move between rooms.
- `who` — list online players.
- `where` — show your current room.
- `help` — list commands and brief usage.
- `quit` — save and disconnect.

## 7) Content & Copy Guidelines
- Tone: welcoming, lightly San Antonio‑flavored (Spanish greetings, local references) while remaining accessible to out‑of‑towners.
- Room descriptions: 1–3 sentences; avoid walls of text; highlight landmarks’ vibe.

## 8) Data Model (MVP)
**Tables (SQLite)**
- `users(id, username, password_hash, created_at, updated_at)` with UNIQUE(username).
- `players(id, user_id, current_room_id, last_seen_at)` — can be merged into users for MVP.
- `rooms(id, name, description)`
- `exits(id, from_room_id, to_room_id, direction)` — constrained to NESW (and named exits if desired).
- (Optional) `messages(id, user_id, scope, room_id, content, created_at)` for audit/logging.

## 9) Architecture & Tech Choices
- **Language/Runtime**: **Python**.
- **Networking**: single‑process, event‑loop or threaded server; broadcast to room/global channels.
- **State**: in‑memory player list per connection; authoritative persistence in SQLite.
- **Config**: `.env` (port, DB path). Default port **2323**.

## 10) Release Plan
**M1 – Skeleton Server (1–2 days)**
- TCP server, telnet connects, echo loop, welcome banner; `help`; hard‑coded `look` output; single room.

**M2 – Accounts & Rooms (1–2 days)**
- Signup/login with hashing; room data seeded in SQLite; movement with exits; `where`/`who`/`look`.

**M3 – Multi‑User Chat (1–2 days)**
- Room and global chat; broadcast plumbing; presence updates.

**M4 – Persistence & Polish (1–2 days)**
- Save last room on `quit`; reconnect resumes; error handling; nicer copy; logs.

## 11) Stretch Goals / V2
- **NPCs**: static NPCs tied to rooms with keyword responses; `talk <npc>`.
- **Tick system**: periodic events (e.g., every 30s) for NPC movement and ambient messages.
- **Extra commands**: `emote <text>`, `whisper <player> <message>`, `get/drop` for simple items.

## 12) Metrics & Success Criteria
- Functional: all MVP commands work as specified; reconnect restores last room.
- Engagement: ≥10 users can connect concurrently; average command round‑trip <200ms locally.
- Stability: zero crashes during a 30‑minute group session with active chat and movement.

## 13) Risks & Mitigations
- **Plain telnet security**: traffic is unencrypted → position for local/demo use; consider SSH or TLS (stunnel) later.
- **Username squatting/griefing**: reserve admin operator; add `/mute` or rate‑limit shouts in V2.
- **Server drops**: implement heartbeat/timeouts; autosave last room on disconnect.

## 14) Open Questions
- Do we want named exits (e.g., `stairs`, `plaza`) in addition to NESW?
- Account deletion/reset flows?

## 15) Appendix — Example Session (for QA)
```
$ telnet localhost 2323
Welcome to the San Antonio MUD
Type `login` or `signup` to begin
> signup
> ...
You appear at The Alamo Plaza
Exits: east, south
> say Hello, anyone here?
[Room] you: Hello, anyone here?
> shout Hola San Antonio!
[Global] you: Hola San Antonio!
> e
River Walk North
Exits: west, south, north
> quit
Goodbye. Your progress has been saved.
```

