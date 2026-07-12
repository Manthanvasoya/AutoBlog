"""
SQLite checkpointing for LangGraph state persistence.
Used only for LangGraph's built-in SqliteSaver, not for application data.
"""

import sqlite3
from pathlib import Path
from typing import Optional, Dict, Any
from langgraph.checkpoint.sqlite import SqliteSaver


class SqliteCheckpointManager:
    """Manager for SQLite checkpointing of LangGraph state"""

    def __init__(self, db_path: str):
        """
        Initialize SQLite checkpoint manager.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self._ensure_db_directory()
        self._saver: Optional[SqliteSaver] = None

    def _ensure_db_directory(self) -> None:
        """Ensure database directory exists"""
        db_dir = Path(self.db_path).parent
        db_dir.mkdir(parents=True, exist_ok=True)

    def get_saver(self) -> SqliteSaver:
        """
        Get LangGraph SqliteSaver instance.
        Lazily initialized on first call.

        Returns:
            SqliteSaver for use in graph configuration
        """
        if self._saver is None:
            self._saver = SqliteSaver(conn=self.db_path)
        return self._saver

    def clear_checkpoints(self, thread_id: str) -> None:
        """
        Clear all checkpoints for a specific thread.

        Args:
            thread_id: Thread ID to clear checkpoints for
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM checkpoints WHERE thread_id = ?", (thread_id,))
            conn.commit()
        finally:
            conn.close()

    def list_threads(self) -> list[str]:
        """
        List all thread IDs with checkpoints.

        Returns:
            List of thread IDs
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT DISTINCT thread_id FROM checkpoints")
            return [row[0] for row in cursor.fetchall()]
        finally:
            conn.close()

    def get_latest_checkpoint(self, thread_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the latest checkpoint for a thread.

        Args:
            thread_id: Thread ID to retrieve

        Returns:
            Checkpoint data or None if not found
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                SELECT checkpoint_data FROM checkpoints
                WHERE thread_id = ?
                ORDER BY checkpoint_id DESC
                LIMIT 1
                """,
                (thread_id,),
            )
            row = cursor.fetchone()
            return row[0] if row else None
        finally:
            conn.close()


def initialize_checkpoint_manager(db_path: str) -> SqliteCheckpointManager:
    """
    Initialize and return SQLite checkpoint manager.

    Args:
        db_path: Path to SQLite database

    Returns:
        Initialized SqliteCheckpointManager
    """
    manager = SqliteCheckpointManager(db_path)
    return manager
