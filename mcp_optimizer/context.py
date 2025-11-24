"""
Context management with pluggable backends
Implements persistent state with TTL and size limits as required
"""

import json
import time
from typing import Any, Dict, Optional, Union
from pathlib import Path
import pickle
import structlog

logger = structlog.get_logger()

class ContextManager:
    """
    Pluggable context management with multiple backends
    Implements the review's requirements for:
    - Pluggable serialization (Redis/SQLite/in-memory)
    - TTL support
    - Size limits
    - Clear context tool
    """

    def __init__(self, backend: str = "memory", ttl: int = 300, size_limit_kb: int = 100):
        self.backend = backend
        self.ttl = ttl  # seconds
        self.size_limit_bytes = size_limit_kb * 1024
        self.last_cache_hit = False

        # Initialize backend
        if backend == "redis":
            self._init_redis()
        elif backend == "sqlite":
            self._init_sqlite()
        else:
            self._init_memory()

        logger.info(
            "context_manager_initialized",
            backend=backend,
            ttl=ttl,
            size_limit_kb=size_limit_kb
        )

    def _init_memory(self):
        """In-memory backend - fastest but not persistent"""
        self.store = {}
        self.metadata = {}

    def _init_redis(self):
        """Redis backend - persistent and distributed"""
        try:
            import redis
            self.redis_client = redis.Redis(
                host='localhost',
                port=6379,
                db=0,
                decode_responses=False  # Store as bytes
            )
            # Test connection
            self.redis_client.ping()
            logger.info("redis_backend_connected")
        except Exception as e:
            logger.warning(f"redis_init_failed", error=str(e))
            # Fallback to memory
            self._init_memory()
            self.backend = "memory"

    def _init_sqlite(self):
        """SQLite backend - persistent and file-based"""
        try:
            import sqlite3
            db_path = Path.home() / ".mcp" / "context.db"
            db_path.parent.mkdir(exist_ok=True)

            self.conn = sqlite3.connect(str(db_path))
            self.cursor = self.conn.cursor()

            # Create table if not exists
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS context (
                    key TEXT PRIMARY KEY,
                    value BLOB,
                    expiry INTEGER,
                    size INTEGER,
                    created_at INTEGER,
                    accessed_at INTEGER
                )
            """)
            self.conn.commit()
            logger.info("sqlite_backend_initialized", path=str(db_path))
        except Exception as e:
            logger.warning(f"sqlite_init_failed", error=str(e))
            self._init_memory()
            self.backend = "memory"

    def get(self, key: str, default: Any = None) -> Any:
        """Get value from context with cache tracking"""

        if self.backend == "memory":
            return self._get_memory(key, default)
        elif self.backend == "redis":
            return self._get_redis(key, default)
        elif self.backend == "sqlite":
            return self._get_sqlite(key, default)

    def _get_memory(self, key: str, default: Any) -> Any:
        """Get from memory with TTL check"""

        if key not in self.store:
            self.last_cache_hit = False
            return default

        meta = self.metadata.get(key, {})
        if meta.get("expiry", float('inf')) < time.time():
            # Expired
            del self.store[key]
            del self.metadata[key]
            self.last_cache_hit = False
            return default

        self.last_cache_hit = True
        return self.store[key]

    def _get_redis(self, key: str, default: Any) -> Any:
        """Get from Redis"""

        try:
            value = self.redis_client.get(f"mcp:context:{key}")
            if value:
                self.last_cache_hit = True
                return pickle.loads(value)
            else:
                self.last_cache_hit = False
                return default
        except Exception as e:
            logger.error("redis_get_failed", key=key, error=str(e))
            return default

    def _get_sqlite(self, key: str, default: Any) -> Any:
        """Get from SQLite with TTL check"""

        try:
            self.cursor.execute(
                "SELECT value, expiry FROM context WHERE key = ?",
                (key,)
            )
            row = self.cursor.fetchone()

            if not row:
                self.last_cache_hit = False
                return default

            value, expiry = row
            if expiry and expiry < time.time():
                # Expired
                self.cursor.execute("DELETE FROM context WHERE key = ?", (key,))
                self.conn.commit()
                self.last_cache_hit = False
                return default

            # Update accessed time
            self.cursor.execute(
                "UPDATE context SET accessed_at = ? WHERE key = ?",
                (int(time.time()), key)
            )
            self.conn.commit()

            self.last_cache_hit = True
            return pickle.loads(value)

        except Exception as e:
            logger.error("sqlite_get_failed", key=key, error=str(e))
            return default

    def set(self, key: str, value: Any) -> bool:
        """Set value in context with size check"""

        # Check size limit
        try:
            serialized = pickle.dumps(value)
            size = len(serialized)

            if size > self.size_limit_bytes:
                logger.warning(
                    "context_size_exceeded",
                    key=key,
                    size=size,
                    limit=self.size_limit_bytes
                )
                return False

        except Exception as e:
            logger.error("serialization_failed", key=key, error=str(e))
            return False

        if self.backend == "memory":
            return self._set_memory(key, value, size)
        elif self.backend == "redis":
            return self._set_redis(key, serialized)
        elif self.backend == "sqlite":
            return self._set_sqlite(key, serialized, size)

    def _set_memory(self, key: str, value: Any, size: int) -> bool:
        """Set in memory with metadata"""

        self.store[key] = value
        self.metadata[key] = {
            "size": size,
            "expiry": time.time() + self.ttl,
            "created_at": time.time()
        }
        return True

    def _set_redis(self, key: str, value_bytes: bytes) -> bool:
        """Set in Redis with TTL"""

        try:
            self.redis_client.setex(
                f"mcp:context:{key}",
                self.ttl,
                value_bytes
            )
            return True
        except Exception as e:
            logger.error("redis_set_failed", key=key, error=str(e))
            return False

    def _set_sqlite(self, key: str, value_bytes: bytes, size: int) -> bool:
        """Set in SQLite with metadata"""

        try:
            now = int(time.time())
            expiry = now + self.ttl

            self.cursor.execute("""
                INSERT OR REPLACE INTO context
                (key, value, expiry, size, created_at, accessed_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (key, value_bytes, expiry, size, now, now))

            self.conn.commit()
            return True

        except Exception as e:
            logger.error("sqlite_set_failed", key=key, error=str(e))
            return False

    def clear(self, pattern: Optional[str] = None) -> int:
        """
        Clear context - implements "clear context" tool from review
        Returns number of items cleared
        """

        if self.backend == "memory":
            if pattern:
                # Clear matching keys
                cleared = 0
                for key in list(self.store.keys()):
                    if pattern in key:
                        del self.store[key]
                        if key in self.metadata:
                            del self.metadata[key]
                        cleared += 1
            else:
                # Clear all
                cleared = len(self.store)
                self.store.clear()
                self.metadata.clear()

        elif self.backend == "redis":
            try:
                if pattern:
                    keys = self.redis_client.keys(f"mcp:context:*{pattern}*")
                else:
                    keys = self.redis_client.keys("mcp:context:*")

                cleared = len(keys)
                if keys:
                    self.redis_client.delete(*keys)

            except Exception as e:
                logger.error("redis_clear_failed", error=str(e))
                cleared = 0

        elif self.backend == "sqlite":
            try:
                if pattern:
                    self.cursor.execute(
                        "DELETE FROM context WHERE key LIKE ?",
                        (f"%{pattern}%",)
                    )
                else:
                    self.cursor.execute("DELETE FROM context")

                cleared = self.cursor.rowcount
                self.conn.commit()

            except Exception as e:
                logger.error("sqlite_clear_failed", error=str(e))
                cleared = 0

        logger.info("context_cleared", pattern=pattern, items_cleared=cleared)
        return cleared

    def get_size(self) -> Dict[str, Any]:
        """Get current context size information"""

        if self.backend == "memory":
            total_size = sum(
                meta.get("size", 0) for meta in self.metadata.values()
            )
            item_count = len(self.store)

        elif self.backend == "redis":
            try:
                keys = self.redis_client.keys("mcp:context:*")
                item_count = len(keys)
                # Estimate size (would need to iterate for exact)
                total_size = item_count * 1000  # Rough estimate

            except:
                item_count = 0
                total_size = 0

        elif self.backend == "sqlite":
            try:
                self.cursor.execute("SELECT COUNT(*), SUM(size) FROM context")
                item_count, total_size = self.cursor.fetchone()
                item_count = item_count or 0
                total_size = total_size or 0

            except:
                item_count = 0
                total_size = 0

        return {
            "items": item_count,
            "size_bytes": total_size,
            "size_kb": total_size / 1024,
            "usage_percent": (total_size / self.size_limit_bytes) * 100,
            "backend": self.backend
        }

    def cleanup_expired(self) -> int:
        """Remove expired entries"""

        if self.backend == "memory":
            now = time.time()
            expired = [
                key for key, meta in self.metadata.items()
                if meta.get("expiry", float('inf')) < now
            ]
            for key in expired:
                del self.store[key]
                del self.metadata[key]
            return len(expired)

        elif self.backend == "sqlite":
            try:
                self.cursor.execute(
                    "DELETE FROM context WHERE expiry < ?",
                    (time.time(),)
                )
                self.conn.commit()
                return self.cursor.rowcount
            except:
                return 0

        # Redis handles TTL automatically
        return 0

    def export(self) -> Dict[str, Any]:
        """Export context for debugging or migration"""

        if self.backend == "memory":
            return {
                "data": self.store.copy(),
                "metadata": self.metadata.copy()
            }
        else:
            # Would implement export for other backends
            return {"backend": self.backend, "export": "not_implemented"}