# -*- coding: utf-8 -*-
"""SQLite Database Manager"""
import sqlite3
import json
import numpy as np
from config import DB_PATH

def init_db():
    """Initialize database tables"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Check if table exists and has behaviors column
    cursor.execute("PRAGMA table_info(feedback)")
    columns = [col[1] for col in cursor.fetchall()]
    
    if 'feedback' not in get_table_names(conn):
        # Create new table with all columns
        cursor.execute("""
            CREATE TABLE feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                feature_vector TEXT NOT NULL,
                predicted_need TEXT NOT NULL,
                actual_need TEXT NOT NULL,
                confidence REAL,
                audio_features TEXT,
                behaviors TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
    elif 'behaviors' not in columns:
        # Add behaviors column to existing table
        cursor.execute("ALTER TABLE feedback ADD COLUMN behaviors TEXT")
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
    """)
    
    cursor.execute("""
        INSERT OR IGNORE INTO settings (key, value) VALUES ('match_threshold', '0.85')
    """)
    
    conn.commit()
    conn.close()

def get_table_names(conn):
    """Get all table names in database"""
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    return [row[0] for row in cursor.fetchall()]

def save_feedback(feature_vector: np.ndarray, predicted_need: str, actual_need: str, 
                  confidence: float = 0.0, audio_features: dict = None, behaviors: list = None):
    """Save user feedback"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    feature_json = json.dumps(feature_vector.tolist())
    audio_features_json = json.dumps(audio_features) if audio_features else "{}"
    behaviors_json = json.dumps(behaviors) if behaviors else "[]"
    
    cursor.execute("""
        INSERT INTO feedback (feature_vector, predicted_need, actual_need, confidence, audio_features, behaviors)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (feature_json, predicted_need, actual_need, confidence, audio_features_json, behaviors_json))
    
    conn.commit()
    conn.close()

def get_all_feedback():
    """Get all feedback records"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, feature_vector, predicted_need, actual_need, confidence, audio_features, behaviors, created_at
        FROM feedback
        ORDER BY created_at DESC
    """)
    
    rows = cursor.fetchall()
    conn.close()
    
    results = []
    for row in rows:
        results.append({
            "id": row[0],
            "feature_vector": np.array(json.loads(row[1])),
            "predicted_need": row[2],
            "actual_need": row[3],
            "confidence": row[4],
            "audio_features": json.loads(row[5]) if row[5] else {},
            "behaviors": json.loads(row[6]) if row[6] else [],
            "created_at": row[7]
        })
    
    return results

def get_feedback_count():
    """Get feedback record count"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM feedback")
    count = cursor.fetchone()[0]
    
    conn.close()
    return count

def get_setting(key: str, default: str = "") -> str:
    """Get setting value"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
    row = cursor.fetchone()
    
    conn.close()
    return row[0] if row else default

def set_setting(key: str, value: str):
    """Set setting value"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)
    """, (key, value))
    
    conn.commit()
    conn.close()
