-- Vehicle Parking System - Data Layer schema (SQLite)
-- Every table here is owned by the Data Layer; the Business Logic Layer
-- reaches it only through app/data/repositories.py.

PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS users (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    name            TEXT    NOT NULL,
    email           TEXT    NOT NULL UNIQUE COLLATE NOCASE,
    password_hash   TEXT    NOT NULL,
    role            TEXT    NOT NULL DEFAULT 'user' CHECK (role IN ('user', 'admin')),
    failed_attempts INTEGER NOT NULL DEFAULT 0,
    locked_until    TEXT,
    created_at      TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS vehicles (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    number      TEXT    NOT NULL UNIQUE COLLATE NOCASE,
    type        TEXT    NOT NULL CHECK (type IN ('car', 'bike', 'truck')),
    owner_name  TEXT    NOT NULL,
    created_at  TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS slots (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    code        TEXT    NOT NULL UNIQUE COLLATE NOCASE,
    slot_type   TEXT    NOT NULL CHECK (slot_type IN ('car', 'bike', 'truck')),
    is_active   INTEGER NOT NULL DEFAULT 1,
    created_at  TEXT    NOT NULL DEFAULT (datetime('now'))
);

-- One row per parking session (entry -> exit -> payment).
CREATE TABLE IF NOT EXISTS parking_sessions (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    vehicle_id  INTEGER NOT NULL REFERENCES vehicles(id),
    slot_id     INTEGER NOT NULL REFERENCES slots(id),
    entry_time  TEXT    NOT NULL,
    exit_time   TEXT,
    fee         REAL,
    status      TEXT    NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'unpaid', 'paid'))
);

-- NFR-08 / SO-02: the database itself refuses a second active session on
-- the same slot, or a vehicle parked in two slots at once.
CREATE UNIQUE INDEX IF NOT EXISTS ux_active_slot
    ON parking_sessions(slot_id) WHERE exit_time IS NULL;
CREATE UNIQUE INDEX IF NOT EXISTS ux_active_vehicle
    ON parking_sessions(vehicle_id) WHERE exit_time IS NULL;

CREATE TABLE IF NOT EXISTS reservations (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    public_id       TEXT    NOT NULL UNIQUE,
    user_id         INTEGER NOT NULL REFERENCES users(id),
    vehicle_id      INTEGER NOT NULL REFERENCES vehicles(id),
    slot_id         INTEGER NOT NULL REFERENCES slots(id),
    start_time      TEXT    NOT NULL,
    end_time        TEXT    NOT NULL,
    status          TEXT    NOT NULL DEFAULT 'confirmed'
                            CHECK (status IN ('confirmed', 'cancelled', 'used', 'expired')),
    idempotency_key TEXT    UNIQUE,
    expiry_notified INTEGER NOT NULL DEFAULT 0,
    created_at      TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS payments (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    public_id       TEXT    NOT NULL UNIQUE,
    session_id      INTEGER NOT NULL REFERENCES parking_sessions(id),
    amount          REAL    NOT NULL,
    method          TEXT    NOT NULL CHECK (method IN ('card', 'upi', 'cash')),
    reference       TEXT,               -- last 4 digits / masked UPI only (C-06)
    status          TEXT    NOT NULL CHECK (status IN ('success', 'failed')),
    idempotency_key TEXT    UNIQUE,
    created_at      TEXT    NOT NULL DEFAULT (datetime('now'))
);

-- NFR-07: rates live in the database so admins can change them without code changes.
CREATE TABLE IF NOT EXISTS rates (
    vehicle_type    TEXT PRIMARY KEY CHECK (vehicle_type IN ('car', 'bike', 'truck')),
    hourly_rate     REAL NOT NULL,
    daily_cap       REAL NOT NULL,
    grace_minutes   INTEGER NOT NULL DEFAULT 10
);

CREATE TABLE IF NOT EXISTS notifications (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    kind        TEXT    NOT NULL,
    message     TEXT    NOT NULL,
    is_read     INTEGER NOT NULL DEFAULT 0,
    created_at  TEXT    NOT NULL DEFAULT (datetime('now'))
);

-- C-09 / SO-05: security-relevant events. Never stores passwords or card data.
CREATE TABLE IF NOT EXISTS audit_log (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    actor_id    INTEGER,
    action      TEXT NOT NULL,
    detail      TEXT,
    ip          TEXT,
    created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS ix_vehicles_user ON vehicles(user_id);
CREATE INDEX IF NOT EXISTS ix_sessions_vehicle ON parking_sessions(vehicle_id);
CREATE INDEX IF NOT EXISTS ix_reservations_slot ON reservations(slot_id, start_time, end_time);
CREATE INDEX IF NOT EXISTS ix_notifications_user ON notifications(user_id, is_read);

INSERT OR IGNORE INTO rates (vehicle_type, hourly_rate, daily_cap, grace_minutes) VALUES
    ('car',   50,  400, 10),
    ('bike',  20,  150, 10),
    ('truck', 100, 800, 10);

-- Server-side login sessions, so logging out really invalidates the cookie (T-12).
CREATE TABLE IF NOT EXISTS login_sessions (
    token       TEXT    PRIMARY KEY,
    user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at  TEXT    NOT NULL DEFAULT (datetime('now')),
    revoked     INTEGER NOT NULL DEFAULT 0
);
