"""Persistent storage layer backed by SQLite + content-addressed blobs."""
import hashlib
import json
import os
import sqlite3
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional


class Storage:
    def __init__(self, root: Path):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.blobs = self.root / "blobs"
        self.blobs.mkdir(exist_ok=True)
        self.db_path = self.root / "stm.db"
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.row_factory = sqlite3.Row
        self._init_schema()

    def _init_schema(self):
        c = self.conn.cursor()
        c.executescript("""
        CREATE TABLE IF NOT EXISTS experiments (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT,
            created_at REAL NOT NULL,
            parent_id TEXT,
            branch_name TEXT,
            seed INTEGER,
            params TEXT NOT NULL,
            state_blob TEXT NOT NULL,
            snapshot_hash TEXT NOT NULL,
            metadata TEXT
        );
        CREATE TABLE IF NOT EXISTS branches (
            name TEXT PRIMARY KEY,
            head_experiment_id TEXT NOT NULL,
            created_at REAL NOT NULL,
            description TEXT
        );
        CREATE TABLE IF NOT EXISTS snapshots (
            id TEXT PRIMARY KEY,
            experiment_id TEXT NOT NULL,
            hash TEXT NOT NULL,
            blob_path TEXT NOT NULL,
            created_at REAL NOT NULL,
            size INTEGER NOT NULL
        );
        CREATE TABLE IF NOT EXISTS runs (
            id TEXT PRIMARY KEY,
            experiment_id TEXT NOT NULL,
            result_blob TEXT NOT NULL,
            result_hash TEXT NOT NULL,
            created_at REAL NOT NULL,
            status TEXT NOT NULL
        );
        """)
        self.conn.commit()

    def blob_path(self, h: str) -> Path:
        return self.blobs / h[:2] / h

    def put_blob(self, data: bytes) -> str:
        h = hashlib.sha256(data).hexdigest()
        p = self.blob_path(h)
        p.parent.mkdir(parents=True, exist_ok=True)
        if not p.exists():
            p.write_bytes(data)
        return h

    def get_blob(self, h: str) -> bytes:
        p = self.blob_path(h)
        if not p.exists():
            raise FileNotFoundError(h)
        return p.read_bytes()

    def verify_blob(self, h: str) -> bool:
        try:
            data = self.get_blob(h)
        except FileNotFoundError:
            return False
        return hashlib.sha256(data).hexdigest() == h

    def close(self):
        self.conn.close()
