import re
import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from src.database import get_db_connection, init_db
MAX_FAILED_ATTEMPTS = 5
LOCKOUT_MINUTES = 5
class AuthManager:
    """Provides secure authentication operations using parameterized SQL queries."""
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path
        init_db(self.db_path)
    @staticmethod
    def is_valid_email(email: str) -> bool:
        """Validates basic email format using standard regex."""
        pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
        return bool(re.match(pattern, email.strip()))
    @staticmethod
    def hash_password(password: str, salt: str) -> str:
        """Hashes a password using PBKDF2-HMAC-SHA256 with 100,000 iterations and salt."""
        key = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt.encode("utf-8"),
            100000
        )
        return key.hex()
    def register_user(self, full_name: str, email: str, password: str, confirm_password: str) -> Dict[str, Any]:
        """Registers a new user with secure password hashing and default free subscription."""
        full_name = full_name.strip()
        email = email.strip().lower()
        if not full_name:
            return {"status": "error", "message": "Full Name is required."}
        if not email or not self.is_valid_email(email):
            return {"status": "error", "message": "Please enter a valid email address."}
        if not password or len(password) < 8:
            return {"status": "error", "message": "Password must be at least 8 characters long."}
        if password != confirm_password:
            return {"status": "error", "message": "Passwords do not match."}
        conn = get_db_connection(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT user_id FROM users WHERE email = ?", (email,))
        if cursor.fetchone():
            conn.close()
            return {"status": "error", "message": "An account with this email address already exists."}
        salt = secrets.token_hex(16)
        password_hash = self.hash_password(password, salt)
        now_str = datetime.now().isoformat()
        try:
            cursor.execute("""
                INSERT INTO users (full_name, email, password_hash, salt, account_status, failed_login_attempts, created_at, updated_at)
                VALUES (?, ?, ?, ?, 'active', 0, ?, ?)
            """, (full_name, email, password_hash, salt, now_str, now_str))
            user_id = cursor.lastrowid
            cursor.execute("""
                INSERT INTO subscriptions (user_id, plan, status, start_date, created_at)
                VALUES (?, 'free', 'active', ?, ?)
            """, (user_id, now_str, now_str))
            conn.commit()
            conn.close()
            return {
                "status": "success",
                "message": "Account created successfully! You can now log in.",
                "user_id": user_id,
                "email": email,
                "full_name": full_name,
                "plan": "free"
            }
        except Exception as e:
            conn.close()
            return {"status": "error", "message": f"Registration failed due to a database error: {str(e)}"}
    def authenticate_user(self, email: str, password: str) -> Dict[str, Any]:
        """Authenticates user with generic error messages and brute-force lockout."""
        email = email.strip().lower()
        generic_error = {"status": "error", "message": "Invalid email or password"}
        if not email or not password:
            return generic_error
        conn = get_db_connection(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT user_id, full_name, email, password_hash, salt, account_status, failed_login_attempts, lockout_until
            FROM users WHERE email = ?
        """, (email,))
        user = cursor.fetchone()
        if not user:
            conn.close()
            return generic_error
        now = datetime.now()
        if user["lockout_until"]:
            try:
                lockout_time = datetime.fromisoformat(user["lockout_until"])
                if now < lockout_time:
                    remaining_sec = int((lockout_time - now).total_seconds())
                    remaining_min = max(1, remaining_sec // 60)
                    conn.close()
                    return {
                        "status": "error",
                        "message": f"Account temporarily locked due to repeated failed login attempts. Try again in {remaining_min} minute(s)."
                    }
            except ValueError:
                pass
        computed_hash = self.hash_password(password, user["salt"])
        if secrets.compare_digest(computed_hash, user["password_hash"]) and user["account_status"] == "active":
            cursor.execute("""
                UPDATE users SET failed_login_attempts = 0, lockout_until = NULL, updated_at = ?
                WHERE user_id = ?
            """, (now.isoformat(), user["user_id"]))
            conn.commit()
            cursor.execute("""
                SELECT plan FROM subscriptions
                WHERE user_id = ? AND status = 'active'
                ORDER BY subscription_id DESC LIMIT 1
            """, (user["user_id"],))
            sub = cursor.fetchone()
            plan = sub["plan"] if sub else "free"
            conn.close()
            return {
                "status": "success",
                "message": "Login successful",
                "user_id": user["user_id"],
                "full_name": user["full_name"],
                "email": user["email"],
                "plan": plan
            }
        else:
            new_failed = (user["failed_login_attempts"] or 0) + 1
            lockout_until_str = None
            if new_failed >= MAX_FAILED_ATTEMPTS:
                lockout_until_str = (now + timedelta(minutes=LOCKOUT_MINUTES)).isoformat()
            cursor.execute("""
                UPDATE users SET failed_login_attempts = ?, lockout_until = ?, updated_at = ?
                WHERE user_id = ?
            """, (new_failed, lockout_until_str, now.isoformat(), user["user_id"]))
            conn.commit()
            conn.close()
            return generic_error