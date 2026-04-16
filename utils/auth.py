import sqlite3
import hashlib
import hmac
import os
import secrets
import smtplib
from email.mime.text import MIMEText
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List

DB_PATH = "tradeiq_auth.db"

SUPER_ADMIN_EMAIL = "chumcred@gmail.com"
SUPER_ADMIN_PASSWORD = "admin123"

# -----------------------------------
# SMTP CONFIG - FILL THESE TO ENABLE EMAIL VERIFICATION
# -----------------------------------
SMTP_ENABLED = True
SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USERNAME = "chumcred@gmail.com"
SMTP_PASSWORD = "sujg suie aqks vtsi"
FROM_EMAIL = "chumcred@gmail.com"


# -----------------------------------
# DB INIT
# -----------------------------------
def get_conn():
    return sqlite3.connect(DB_PATH, check_same_thread=False)


def init_auth_db():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            company_name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            company_address TEXT NOT NULL,
            phone_number TEXT NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'user',
            is_email_verified INTEGER NOT NULL DEFAULT 0,
            verification_token TEXT,
            verification_expiry TEXT,
            created_at TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()

    bootstrap_super_admin()


def bootstrap_super_admin():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("SELECT id FROM users WHERE email = ?", (SUPER_ADMIN_EMAIL.lower().strip(),))
    existing = cur.fetchone()

    if not existing:
        password_hash = hash_password(SUPER_ADMIN_PASSWORD)
        cur.execute("""
            INSERT INTO users (
                name,
                company_name,
                email,
                company_address,
                phone_number,
                password_hash,
                role,
                is_email_verified,
                verification_token,
                verification_expiry,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            "Kunle Adegbie",
            "Chumcred",
            SUPER_ADMIN_EMAIL.lower().strip(),
            "Lagos, Nigeria",
            "00000000000",
            password_hash,
            "super_admin",
            1,
            None,
            None,
            datetime.utcnow().isoformat()
        ))
        conn.commit()

    conn.close()


# -----------------------------------
# PASSWORD HELPERS
# -----------------------------------
def hash_password(password: str) -> str:
    salt = os.urandom(16)
    key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100000)
    return salt.hex() + ":" + key.hex()


def verify_password(password: str, stored_hash: str) -> bool:
    try:
        salt_hex, key_hex = stored_hash.split(":")
        salt = bytes.fromhex(salt_hex)
        expected_key = bytes.fromhex(key_hex)
        check_key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100000)
        return hmac.compare_digest(expected_key, check_key)
    except Exception:
        return False


# -----------------------------------
# EMAIL VERIFICATION
# -----------------------------------
def generate_verification_token() -> str:
    return secrets.token_urlsafe(32)


def send_verification_email(email: str, token: str):
    if not SMTP_ENABLED:
        return

    verify_link = f"http://localhost:8501/?verify_token={token}"

    body = f"""
Hello,

Please verify your TradeIQ account by clicking the link below:

{verify_link}

This link expires in 24 hours.

Regards,
TradeIQ Team
"""

    msg = MIMEText(body)
    msg["Subject"] = "Verify your TradeIQ account"
    msg["From"] = FROM_EMAIL
    msg["To"] = email

    server = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
    server.starttls()
    server.login(SMTP_USERNAME, SMTP_PASSWORD)
    server.sendmail(FROM_EMAIL, [email], msg.as_string())
    server.quit()


def verify_email_token(token: str) -> bool:
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        SELECT id, verification_expiry
        FROM users
        WHERE verification_token = ?
    """, (token,))
    row = cur.fetchone()

    if not row:
        conn.close()
        return False

    user_id, expiry = row

    if not expiry:
        conn.close()
        return False

    if datetime.utcnow() > datetime.fromisoformat(expiry):
        conn.close()
        return False

    cur.execute("""
        UPDATE users
        SET is_email_verified = 1,
            verification_token = NULL,
            verification_expiry = NULL
        WHERE id = ?
    """, (user_id,))
    conn.commit()
    conn.close()
    return True


# -----------------------------------
# USER CRUD
# -----------------------------------
def create_user(
    name: str,
    company_name: str,
    email: str,
    company_address: str,
    phone_number: str,
    password: str
) -> Dict[str, Any]:
    conn = get_conn()
    cur = conn.cursor()

    normalized_email = email.lower().strip()

    cur.execute("SELECT id FROM users WHERE email = ?", (normalized_email,))
    if cur.fetchone():
        conn.close()
        return {"success": False, "message": "Email already exists."}

    token = generate_verification_token()
    expiry = (datetime.utcnow() + timedelta(hours=24)).isoformat()

    cur.execute("""
        INSERT INTO users (
            name,
            company_name,
            email,
            company_address,
            phone_number,
            password_hash,
            role,
            is_email_verified,
            verification_token,
            verification_expiry,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        name.strip(),
        company_name.strip(),
        normalized_email,
        company_address.strip(),
        phone_number.strip(),
        hash_password(password),
        "user",
        0 if SMTP_ENABLED else 1,
        token if SMTP_ENABLED else None,
        expiry if SMTP_ENABLED else None,
        datetime.utcnow().isoformat()
    ))

    conn.commit()
    conn.close()

    if SMTP_ENABLED:
        send_verification_email(normalized_email, token)
        return {
            "success": True,
            "message": "Signup successful. Verification email sent."
        }

    return {
        "success": True,
        "message": "Signup successful. Email verification is currently disabled, so your account is active."
    }


def authenticate_user(email: str, password: str) -> Dict[str, Any]:
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        SELECT id, name, company_name, email, company_address, phone_number,
               password_hash, role, is_email_verified
        FROM users
        WHERE email = ?
    """, (email.lower().strip(),))

    row = cur.fetchone()
    conn.close()

    if not row:
        return {"success": False, "message": "Invalid email or password."}

    user = {
        "id": row[0],
        "name": row[1],
        "company_name": row[2],
        "email": row[3],
        "company_address": row[4],
        "phone_number": row[5],
        "password_hash": row[6],
        "role": row[7],
        "is_email_verified": bool(row[8]),
    }

    if not verify_password(password, user["password_hash"]):
        return {"success": False, "message": "Invalid email or password."}

    if not user["is_email_verified"]:
        return {"success": False, "message": "Please verify your email before logging in."}

    user.pop("password_hash", None)
    return {"success": True, "user": user}


def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        SELECT id, name, company_name, email, company_address, phone_number,
               role, is_email_verified, created_at
        FROM users
        WHERE email = ?
    """, (email.lower().strip(),))

    row = cur.fetchone()
    conn.close()

    if not row:
        return None

    return {
        "id": row[0],
        "name": row[1],
        "company_name": row[2],
        "email": row[3],
        "company_address": row[4],
        "phone_number": row[5],
        "role": row[6],
        "is_email_verified": bool(row[7]),
        "created_at": row[8],
    }


def get_all_users() -> List[Dict[str, Any]]:
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            id,
            name,
            company_name,
            email,
            company_address,
            phone_number,
            role,
            is_email_verified,
            created_at
        FROM users
        ORDER BY created_at DESC
    """)

    rows = cur.fetchall()
    conn.close()

    results = []
    for row in rows:
        results.append({
            "id": row[0],
            "name": row[1],
            "company_name": row[2],
            "email": row[3],
            "company_address": row[4],
            "phone_number": row[5],
            "role": row[6],
            "is_email_verified": bool(row[7]),
            "created_at": row[8],
        })
    return results


def create_institution_admin(
    name: str,
    company_name: str,
    email: str,
    company_address: str,
    phone_number: str,
    password: str
) -> Dict[str, Any]:
    conn = get_conn()
    cur = conn.cursor()

    normalized_email = email.lower().strip()

    cur.execute("SELECT id FROM users WHERE email = ?", (normalized_email,))
    if cur.fetchone():
        conn.close()
        return {"success": False, "message": "Email already exists."}

    cur.execute("""
        INSERT INTO users (
            name,
            company_name,
            email,
            company_address,
            phone_number,
            password_hash,
            role,
            is_email_verified,
            verification_token,
            verification_expiry,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        name.strip(),
        company_name.strip(),
        normalized_email,
        company_address.strip(),
        phone_number.strip(),
        hash_password(password),
        "institution_admin",
        1,
        None,
        None,
        datetime.utcnow().isoformat()
    ))

    conn.commit()
    conn.close()

    return {
        "success": True,
        "message": "Institution admin created successfully."
    }


def create_institution_user(
    institution_name: str,
    name: str,
    email: str,
    company_address: str,
    phone_number: str,
    password: str
) -> Dict[str, Any]:
    conn = get_conn()
    cur = conn.cursor()

    normalized_email = email.lower().strip()

    cur.execute("SELECT id FROM users WHERE email = ?", (normalized_email,))
    if cur.fetchone():
        conn.close()
        return {"success": False, "message": "Email already exists."}

    cur.execute("""
        INSERT INTO users (
            name,
            company_name,
            email,
            company_address,
            phone_number,
            password_hash,
            role,
            is_email_verified,
            verification_token,
            verification_expiry,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        name.strip(),
        institution_name.strip(),
        normalized_email,
        company_address.strip(),
        phone_number.strip(),
        hash_password(password),
        "user",
        1,
        None,
        None,
        datetime.utcnow().isoformat()
    ))

    conn.commit()
    conn.close()

    return {
        "success": True,
        "message": "Institution user created successfully."
    }


def get_users_by_company(company_name: str) -> List[Dict[str, Any]]:
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            id,
            name,
            company_name,
            email,
            company_address,
            phone_number,
            role,
            is_email_verified,
            created_at
        FROM users
        WHERE company_name = ?
        ORDER BY created_at DESC
    """, (company_name.strip(),))

    rows = cur.fetchall()
    conn.close()

    results = []
    for row in rows:
        results.append({
            "id": row[0],
            "name": row[1],
            "company_name": row[2],
            "email": row[3],
            "company_address": row[4],
            "phone_number": row[5],
            "role": row[6],
            "is_email_verified": bool(row[7]),
            "created_at": row[8],
        })
    return results