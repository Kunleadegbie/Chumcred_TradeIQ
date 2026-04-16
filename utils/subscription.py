import os
import sqlite3
import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any

DB_PATH = "tradeiq_auth.db"
UPLOAD_DIR = "uploads/subscriptions"

SUBSCRIPTION_PLANS = {
    "Basic": 25000,
    "Professional": 50000,
    "Institutional": 150000,
}


def get_conn():
    return sqlite3.connect(DB_PATH, check_same_thread=False)


def init_subscription_db():
    os.makedirs(UPLOAD_DIR, exist_ok=True)

    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS subscriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_email TEXT NOT NULL,
            user_name TEXT NOT NULL,
            institution_name TEXT NOT NULL,
            phone_number TEXT,
            plan_name TEXT NOT NULL,
            amount REAL NOT NULL,
            payment_reference TEXT,
            evidence_file TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            admin_note TEXT,
            approved_by TEXT,
            submitted_at TEXT NOT NULL,
            approved_at TEXT
        )
    """)

    conn.commit()
    conn.close()


def save_payment_evidence(uploaded_file, user_email: str) -> str:
    os.makedirs(UPLOAD_DIR, exist_ok=True)

    ext = os.path.splitext(uploaded_file.name)[1].lower()
    safe_email = user_email.replace("@", "_at_").replace(".", "_")
    unique_name = f"{safe_email}_{uuid.uuid4().hex}{ext}"
    save_path = os.path.join(UPLOAD_DIR, unique_name)

    with open(save_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    return save_path


def create_subscription_request(
    user_email: str,
    user_name: str,
    institution_name: str,
    phone_number: str,
    plan_name: str,
    amount: float,
    payment_reference: str,
    evidence_file: str,
):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO subscriptions (
            user_email,
            user_name,
            institution_name,
            phone_number,
            plan_name,
            amount,
            payment_reference,
            evidence_file,
            status,
            admin_note,
            approved_by,
            submitted_at,
            approved_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'pending', NULL, NULL, ?, NULL)
    """, (
        user_email,
        user_name,
        institution_name,
        phone_number,
        plan_name,
        amount,
        payment_reference,
        evidence_file,
        datetime.utcnow().isoformat(),
    ))

    conn.commit()
    conn.close()


def get_user_subscription_requests(user_email: str) -> List[Dict[str, Any]]:
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            id,
            plan_name,
            amount,
            payment_reference,
            evidence_file,
            status,
            admin_note,
            submitted_at,
            approved_at
        FROM subscriptions
        WHERE user_email = ?
        ORDER BY submitted_at DESC
    """, (user_email,))

    rows = cur.fetchall()
    conn.close()

    results = []
    for row in rows:
        results.append({
            "id": row[0],
            "plan_name": row[1],
            "amount": row[2],
            "payment_reference": row[3],
            "evidence_file": row[4],
            "status": row[5],
            "admin_note": row[6],
            "submitted_at": row[7],
            "approved_at": row[8],
        })

    return results


def get_latest_active_or_pending_status(user_email: str) -> Optional[str]:
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        SELECT status
        FROM subscriptions
        WHERE user_email = ?
        ORDER BY submitted_at DESC
        LIMIT 1
    """, (user_email,))

    row = cur.fetchone()
    conn.close()

    return row[0] if row else None


def get_all_subscription_requests(status_filter: Optional[str] = None) -> List[Dict[str, Any]]:
    conn = get_conn()
    cur = conn.cursor()

    if status_filter and status_filter.lower() != "all":
        cur.execute("""
            SELECT
                id,
                user_email,
                user_name,
                institution_name,
                phone_number,
                plan_name,
                amount,
                payment_reference,
                evidence_file,
                status,
                admin_note,
                approved_by,
                submitted_at,
                approved_at
            FROM subscriptions
            WHERE status = ?
            ORDER BY submitted_at DESC
        """, (status_filter.lower().strip(),))
    else:
        cur.execute("""
            SELECT
                id,
                user_email,
                user_name,
                institution_name,
                phone_number,
                plan_name,
                amount,
                payment_reference,
                evidence_file,
                status,
                admin_note,
                approved_by,
                submitted_at,
                approved_at
            FROM subscriptions
            ORDER BY submitted_at DESC
        """)

    rows = cur.fetchall()
    conn.close()

    results = []
    for row in rows:
        results.append({
            "id": row[0],
            "user_email": row[1],
            "user_name": row[2],
            "institution_name": row[3],
            "phone_number": row[4],
            "plan_name": row[5],
            "amount": row[6],
            "payment_reference": row[7],
            "evidence_file": row[8],
            "status": row[9],
            "admin_note": row[10],
            "approved_by": row[11],
            "submitted_at": row[12],
            "approved_at": row[13],
        })
    return results


def get_subscription_request_by_id(request_id: int) -> Optional[Dict[str, Any]]:
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            id,
            user_email,
            user_name,
            institution_name,
            phone_number,
            plan_name,
            amount,
            payment_reference,
            evidence_file,
            status,
            admin_note,
            approved_by,
            submitted_at,
            approved_at
        FROM subscriptions
        WHERE id = ?
    """, (request_id,))

    row = cur.fetchone()
    conn.close()

    if not row:
        return None

    return {
        "id": row[0],
        "user_email": row[1],
        "user_name": row[2],
        "institution_name": row[3],
        "phone_number": row[4],
        "plan_name": row[5],
        "amount": row[6],
        "payment_reference": row[7],
        "evidence_file": row[8],
        "status": row[9],
        "admin_note": row[10],
        "approved_by": row[11],
        "submitted_at": row[12],
        "approved_at": row[13],
    }


def approve_subscription_request(request_id: int, admin_email: str, admin_note: str = "") -> Dict[str, Any]:
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("SELECT id, status FROM subscriptions WHERE id = ?", (request_id,))
    row = cur.fetchone()

    if not row:
        conn.close()
        return {"success": False, "message": "Subscription request not found."}

    _, current_status = row
    if current_status == "approved":
        conn.close()
        return {"success": False, "message": "This request has already been approved."}

    cur.execute("""
        UPDATE subscriptions
        SET status = 'approved',
            admin_note = ?,
            approved_by = ?,
            approved_at = ?
        WHERE id = ?
    """, (
        admin_note.strip() if admin_note else None,
        admin_email.strip().lower(),
        datetime.utcnow().isoformat(),
        request_id
    ))

    conn.commit()
    conn.close()

    return {"success": True, "message": "Subscription request approved successfully."}


def reject_subscription_request(request_id: int, admin_email: str, admin_note: str = "") -> Dict[str, Any]:
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("SELECT id, status FROM subscriptions WHERE id = ?", (request_id,))
    row = cur.fetchone()

    if not row:
        conn.close()
        return {"success": False, "message": "Subscription request not found."}

    _, current_status = row
    if current_status == "rejected":
        conn.close()
        return {"success": False, "message": "This request has already been rejected."}

    cur.execute("""
        UPDATE subscriptions
        SET status = 'rejected',
            admin_note = ?,
            approved_by = ?,
            approved_at = ?
        WHERE id = ?
    """, (
        admin_note.strip() if admin_note else None,
        admin_email.strip().lower(),
        datetime.utcnow().isoformat(),
        request_id
    ))

    conn.commit()
    conn.close()

    return {"success": True, "message": "Subscription request rejected successfully."}