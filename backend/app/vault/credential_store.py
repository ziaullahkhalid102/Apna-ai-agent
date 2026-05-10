"""Encrypted credential vault using Fernet symmetric encryption + SQLite."""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone

import aiosqlite
from cryptography.fernet import Fernet

from app.config import settings

logger = logging.getLogger(__name__)

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS credentials (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    service TEXT NOT NULL,
    username TEXT NOT NULL,
    encrypted_data BLOB NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE(service, username)
)
"""


class CredentialStore:
    """Encrypted local credential vault.

    Stores service credentials (email, password, tokens) encrypted at rest
    using Fernet (AES-128-CBC). The encryption key is stored separately
    from the database.
    """

    def __init__(
        self,
        db_path: str | None = None,
        key_path: str | None = None,
    ) -> None:
        self._db_path = db_path or settings.vault_db_path
        self._key_path = key_path or settings.vault_key_path
        self._fernet: Fernet | None = None
        self._db: aiosqlite.Connection | None = None

    async def initialize(self) -> None:
        os.makedirs(os.path.dirname(self._db_path), exist_ok=True)
        os.makedirs(os.path.dirname(self._key_path), exist_ok=True)

        if os.path.exists(self._key_path):
            with open(self._key_path, "rb") as f:
                key = f.read()
        else:
            key = Fernet.generate_key()
            fd = os.open(self._key_path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
            with os.fdopen(fd, "wb") as f:
                f.write(key)

        self._fernet = Fernet(key)
        self._db = await aiosqlite.connect(self._db_path)
        await self._db.execute(CREATE_TABLE_SQL)
        await self._db.commit()
        logger.info("Credential store initialized")

    async def close(self) -> None:
        if self._db:
            await self._db.close()
            self._db = None

    async def store(
        self,
        service: str,
        username: str,
        credentials: dict[str, str],
    ) -> None:
        if not self._fernet or not self._db:
            raise RuntimeError("Credential store not initialized")

        encrypted = self._fernet.encrypt(json.dumps(credentials).encode())
        now = datetime.now(timezone.utc).isoformat()

        await self._db.execute(
            """INSERT INTO credentials (service, username, encrypted_data, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?)
               ON CONFLICT(service, username) DO UPDATE SET
                   encrypted_data = excluded.encrypted_data,
                   updated_at = excluded.updated_at""",
            (service, username, encrypted, now, now),
        )
        await self._db.commit()
        logger.info("Stored credentials for %s/%s", service, username)

    async def retrieve(self, service: str, username: str) -> dict[str, str] | None:
        if not self._fernet or not self._db:
            raise RuntimeError("Credential store not initialized")

        cursor = await self._db.execute(
            "SELECT encrypted_data FROM credentials WHERE service = ? AND username = ?",
            (service, username),
        )
        row = await cursor.fetchone()
        if not row:
            return None

        decrypted = self._fernet.decrypt(row[0])
        return json.loads(decrypted.decode())

    async def delete(self, service: str, username: str) -> bool:
        if not self._db:
            raise RuntimeError("Credential store not initialized")

        cursor = await self._db.execute(
            "DELETE FROM credentials WHERE service = ? AND username = ?",
            (service, username),
        )
        await self._db.commit()
        deleted = cursor.rowcount > 0
        if deleted:
            logger.info("Deleted credentials for %s/%s", service, username)
        return deleted

    async def list_services(self) -> list[dict[str, str]]:
        if not self._db:
            raise RuntimeError("Credential store not initialized")

        cursor = await self._db.execute(
            "SELECT service, username, created_at, updated_at FROM credentials ORDER BY service"
        )
        rows = await cursor.fetchall()
        return [
            {
                "service": row[0],
                "username": row[1],
                "created_at": row[2],
                "updated_at": row[3],
            }
            for row in rows
        ]
