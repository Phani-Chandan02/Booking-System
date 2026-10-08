import sqlite3
import os
import hashlib
import binascii

DB_PATH = os.getenv("DB_PATH", os.path.join(os.path.dirname(__file__), "booking_system.db"))

def hash_password(password: str, salt: bytes = None) -> tuple[str, str]:
    if salt is None:
        salt = os.urandom(16)
    kdf = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100000)
    return binascii.hexlify(kdf).decode("utf-8"), binascii.hexlify(salt).decode("utf-8")

def verify_password(stored_hash: str, salt_hex: str, provided_password: str) -> bool:
    salt = binascii.unhexlify(salt_hex.encode("utf-8"))
    kdf = hashlib.pbkdf2_hmac("sha256", provided_password.encode("utf-8"), salt, 100000)
    return binascii.hexlify(kdf).decode("utf-8") == stored_hash

def get_db_connection(timeout: float = 5.0) -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, timeout=timeout)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA journal_mode = WAL;")
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.executescript("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        salt TEXT NOT NULL,
        role TEXT NOT NULL CHECK(role IN ('student', 'faculty', 'admin')),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS services (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        description TEXT NOT NULL,
        duration_minutes INTEGER NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS time_slots (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        service_id INTEGER NOT NULL,
        provider_id INTEGER NOT NULL,
        slot_date TEXT NOT NULL,
        start_time TEXT NOT NULL,
        end_time TEXT NOT NULL,
        is_booked INTEGER NOT NULL DEFAULT 0,
        FOREIGN KEY (service_id) REFERENCES services(id) ON DELETE CASCADE,
        FOREIGN KEY (provider_id) REFERENCES users(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS appointments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        slot_id INTEGER NOT NULL,
        status TEXT NOT NULL CHECK(status IN ('CONFIRMED', 'CANCELLED', 'RESCHEDULED', 'COMPLETED')),
        booked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY (slot_id) REFERENCES time_slots(id) ON DELETE CASCADE
    );

    -- Crucial Database Security Control: Prevents two active/confirmed appointments for same slot
    CREATE UNIQUE INDEX IF NOT EXISTS idx_unique_confirmed_slot 
    ON appointments(slot_id) WHERE status = 'CONFIRMED';

    CREATE TABLE IF NOT EXISTS audit_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        action TEXT NOT NULL,
        status TEXT NOT NULL,
        ip_address TEXT,
        details TEXT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Seed default users if table is empty
    cursor.execute("SELECT COUNT(*) FROM users;")
    if cursor.fetchone()[0] == 0:
        demo_users = [
            ("Student User", "student@booking.com", "Student@123", "student"),
            ("Dr. Alan Smith (Faculty)", "faculty@booking.com", "Faculty@123", "faculty"),
            ("System Administrator", "admin@booking.com", "Admin@123", "admin"),
            ("Second Student User", "student2@booking.com", "Student@123", "student"),
        ]
        for name, email, pwd, role in demo_users:
            pwd_hash, salt = hash_password(pwd)
            cursor.execute(
                "INSERT INTO users (name, email, password_hash, salt, role) VALUES (?, ?, ?, ?, ?)",
                (name, email, pwd_hash, salt, role)
            )

        demo_services = [
            ("Academic Advising & Course Review", "One-on-one session with faculty mentor for degree planning and course approvals", 30),
            ("Capstone Project Consultation", "Technical architecture and security review for senior research projects", 45),
            ("Lab Exam Evaluation & Grievance", "Formal lab exam re-evaluation and feedback discussion", 20),
        ]
        for sname, sdesc, sdur in demo_services:
            cursor.execute(
                "INSERT INTO services (name, description, duration_minutes) VALUES (?, ?, ?)",
                (sname, sdesc, sdur)
            )

        # Seed sample time slots for faculty (id=2)
        demo_slots = [
            (1, 2, "2026-10-15", "09:00", "09:30"),
            (1, 2, "2026-10-15", "10:00", "10:30"),
            (2, 2, "2026-10-15", "11:00", "11:45"),
            (2, 2, "2026-10-15", "14:00", "14:45"),
            (3, 2, "2026-10-16", "10:00", "10:20"),
            (3, 2, "2026-10-16", "10:30", "10:50"),
            (1, 2, "2026-10-16", "15:00", "15:30"),
        ]
        for sid, pid, sdate, stime, etime in demo_slots:
            cursor.execute(
                "INSERT INTO time_slots (service_id, provider_id, slot_date, start_time, end_time, is_booked) VALUES (?, ?, ?, ?, ?, 0)",
                (sid, pid, sdate, stime, etime)
            )

    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("Database initialized and seeded successfully.")
