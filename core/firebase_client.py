"""
Craftora Firebase Client
Saves generated patterns to Firestore automatically.
"""

import os
import json
from datetime import datetime, timezone
from typing import Optional
import firebase_admin
from firebase_admin import credentials, firestore
from dotenv import load_dotenv

load_dotenv()

_db = None


def _get_db():
    global _db
    if _db is None:
        cred_path = os.getenv("FIREBASE_CREDENTIALS_PATH", "firebase_credentials.json")
        if not firebase_admin._apps:
            try:
                cred = credentials.Certificate(cred_path)
                firebase_admin.initialize_app(cred)
            except Exception as e:
                print(f"[Firebase] Could not initialize: {e}")
                return None
        _db = firestore.client()
    return _db


async def save_pattern(pattern_data: dict) -> Optional[str]:
    """
    Save a generated pattern to Firestore.
    Returns the Firestore document ID or None if failed.
    """
    db = _get_db()
    if db is None:
        print("[Firebase] Skipping save — Firebase not configured.")
        return None

    try:
        doc_data = {
            **pattern_data,
            "createdAt":  datetime.now(timezone.utc).isoformat(),
            "source":     "ai_generated",
            "isFree":     True,
            "isFeatured": False,
            "isTrending": False,
            "saves":      0,
            "views":      0,
            "rating":     0.0,
        }
        # Remove non-serializable fields
        doc_data.pop("validation", None)
        doc_data.pop("pdf_url",    None)

        ref = db.collection("patterns").document()
        ref.set(doc_data)
        print(f"[Firebase] Pattern saved: {ref.id}")
        return ref.id

    except Exception as e:
        print(f"[Firebase] Save failed: {e}")
        return None


async def get_pattern(pattern_id: str) -> Optional[dict]:
    db = _get_db()
    if db is None:
        return None
    try:
        doc = db.collection("patterns").document(pattern_id).get()
        if doc.exists:
            return {"id": doc.id, **doc.to_dict()}
        return None
    except Exception as e:
        print(f"[Firebase] Get failed: {e}")
        return None


async def list_patterns(craft_type: Optional[str] = None, limit: int = 20) -> list:
    db = _get_db()
    if db is None:
        return []
    try:
        q = db.collection("patterns").order_by("createdAt", direction=firestore.Query.DESCENDING)
        if craft_type:
            q = q.where("craftType", "==", craft_type)
        q = q.limit(limit)
        docs = q.stream()
        return [{"id": d.id, **d.to_dict()} for d in docs]
    except Exception as e:
        print(f"[Firebase] List failed: {e}")
        return []
