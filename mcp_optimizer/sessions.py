"""
Session management with TTL, concurrency control, and bounded growth
Addresses critique about state persistence issues
"""

import uuid
import time
import json
import threading
from typing import Dict, Any, Optional, List, Set
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from collections import OrderedDict
import structlog

logger = structlog.get_logger()

@dataclass
class Session:
    """
    Scoped session with automatic pruning
    Addresses critique about unbounded context growth
    """
    session_id: str
    created_at: float
    last_accessed: float
    ttl_seconds: int
    max_size_kb: int
    owner: Optional[str] = None
    context: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    access_count: int = 0
    lock: threading.RLock = field(default_factory=threading.RLock)

    def is_expired(self) -> bool:
        """Check if session has expired"""
        return (time.time() - self.last_accessed) > self.ttl_seconds

    def size_bytes(self) -> int:
        """Calculate current session size"""
        return len(json.dumps(self.context))

    def is_over_limit(self) -> bool:
        """Check if session exceeds size limit"""
        return self.size_bytes() > (self.max_size_kb * 1024)

    def touch(self) -> None:
        """Update last accessed time"""
        with self.lock:
            self.last_accessed = time.time()
            self.access_count += 1

    def get(self, key: str, default: Any = None) -> Any:
        """Thread-safe get"""
        with self.lock:
            self.touch()
            return self.context.get(key, default)

    def set(self, key: str, value: Any) -> bool:
        """Thread-safe set with size check"""
        with self.lock:
            # Temporarily add to check size
            temp_context = self.context.copy()
            temp_context[key] = value

            temp_size = len(json.dumps(temp_context))
            if temp_size > (self.max_size_kb * 1024):
                logger.warning(
                    "session_size_exceeded",
                    session_id=self.session_id,
                    size_kb=temp_size / 1024,
                    limit_kb=self.max_size_kb
                )
                return False

            self.context[key] = value
            self.touch()
            return True

    def clear(self) -> None:
        """Clear session context"""
        with self.lock:
            self.context.clear()
            self.touch()

    def snapshot(self) -> Dict[str, Any]:
        """Create session snapshot for persistence"""
        with self.lock:
            return {
                "session_id": self.session_id,
                "created_at": self.created_at,
                "last_accessed": self.last_accessed,
                "owner": self.owner,
                "context": self.context.copy(),
                "metadata": self.metadata.copy(),
                "access_count": self.access_count,
                "size_bytes": self.size_bytes()
            }

    def restore(self, snapshot: Dict[str, Any]) -> None:
        """Restore from snapshot"""
        with self.lock:
            self.context = snapshot.get("context", {})
            self.metadata = snapshot.get("metadata", {})
            self.access_count = snapshot.get("access_count", 0)
            self.touch()

class SessionManager:
    """
    Multi-session manager with concurrency and TTL
    Solves the critique's concerns about session isolation and growth
    """

    def __init__(self,
                 default_ttl: int = 3600,  # 1 hour
                 max_sessions: int = 100,
                 max_session_size_kb: int = 100,
                 enable_persistence: bool = False):

        self.default_ttl = default_ttl
        self.max_sessions = max_sessions
        self.max_session_size_kb = max_session_size_kb
        self.enable_persistence = enable_persistence

        # Thread-safe session storage
        self.sessions: OrderedDict[str, Session] = OrderedDict()
        self.lock = threading.RLock()

        # Session index by owner
        self.owner_sessions: Dict[str, Set[str]] = {}

        # Start cleanup thread
        self.cleanup_thread = threading.Thread(
            target=self._cleanup_worker,
            daemon=True
        )
        self.cleanup_thread.start()

        logger.info(
            "session_manager_initialized",
            max_sessions=max_sessions,
            default_ttl=default_ttl
        )

    def create_session(self,
                       owner: Optional[str] = None,
                       ttl: Optional[int] = None) -> str:
        """
        Create new session with automatic cleanup
        Returns session_id
        """

        session_id = str(uuid.uuid4())
        ttl = ttl or self.default_ttl

        session = Session(
            session_id=session_id,
            created_at=time.time(),
            last_accessed=time.time(),
            ttl_seconds=ttl,
            max_size_kb=self.max_session_size_kb,
            owner=owner
        )

        with self.lock:
            # Enforce max sessions (LRU eviction)
            if len(self.sessions) >= self.max_sessions:
                self._evict_lru()

            self.sessions[session_id] = session

            # Index by owner
            if owner:
                if owner not in self.owner_sessions:
                    self.owner_sessions[owner] = set()
                self.owner_sessions[owner].add(session_id)

        logger.info(
            "session_created",
            session_id=session_id,
            owner=owner,
            ttl=ttl
        )

        return session_id

    def get_session(self, session_id: str) -> Optional[Session]:
        """Get session if exists and not expired"""

        with self.lock:
            session = self.sessions.get(session_id)

            if session:
                if session.is_expired():
                    self._remove_session(session_id)
                    return None

                # Move to end (LRU)
                self.sessions.move_to_end(session_id)
                return session

            return None

    def list_sessions(self, owner: Optional[str] = None) -> List[Dict[str, Any]]:
        """List active sessions, optionally filtered by owner"""

        with self.lock:
            sessions = []

            if owner and owner in self.owner_sessions:
                session_ids = self.owner_sessions[owner]
            else:
                session_ids = self.sessions.keys()

            for session_id in session_ids:
                session = self.sessions.get(session_id)
                if session and not session.is_expired():
                    sessions.append({
                        "session_id": session_id,
                        "owner": session.owner,
                        "created_at": datetime.fromtimestamp(session.created_at).isoformat(),
                        "last_accessed": datetime.fromtimestamp(session.last_accessed).isoformat(),
                        "ttl_remaining": max(0, session.ttl_seconds - (time.time() - session.last_accessed)),
                        "size_kb": session.size_bytes() / 1024,
                        "access_count": session.access_count
                    })

            return sessions

    def reset_session(self, session_id: str) -> bool:
        """Reset session context while preserving session"""

        session = self.get_session(session_id)
        if session:
            session.clear()
            logger.info("session_reset", session_id=session_id)
            return True
        return False

    def extend_session(self, session_id: str, additional_ttl: int) -> bool:
        """Extend session TTL"""

        session = self.get_session(session_id)
        if session:
            with session.lock:
                session.ttl_seconds += additional_ttl
                session.touch()
            logger.info(
                "session_extended",
                session_id=session_id,
                new_ttl=session.ttl_seconds
            )
            return True
        return False

    def snapshot_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Create session snapshot for backup/restore"""

        session = self.get_session(session_id)
        if session:
            return session.snapshot()
        return None

    def restore_session(self, snapshot: Dict[str, Any]) -> str:
        """Restore session from snapshot"""

        session_id = snapshot.get("session_id", str(uuid.uuid4()))

        session = Session(
            session_id=session_id,
            created_at=snapshot.get("created_at", time.time()),
            last_accessed=time.time(),
            ttl_seconds=self.default_ttl,
            max_size_kb=self.max_session_size_kb,
            owner=snapshot.get("owner")
        )

        session.restore(snapshot)

        with self.lock:
            self.sessions[session_id] = session

        logger.info("session_restored", session_id=session_id)
        return session_id

    def _evict_lru(self) -> None:
        """Evict least recently used session"""

        if self.sessions:
            # OrderedDict maintains order, first item is LRU
            lru_id = next(iter(self.sessions))
            self._remove_session(lru_id)
            logger.info("session_evicted_lru", session_id=lru_id)

    def _remove_session(self, session_id: str) -> None:
        """Remove session and clean up indexes"""

        with self.lock:
            session = self.sessions.pop(session_id, None)

            if session:
                # Remove from owner index
                if session.owner and session.owner in self.owner_sessions:
                    self.owner_sessions[session.owner].discard(session_id)

                    # Clean up empty owner entries
                    if not self.owner_sessions[session.owner]:
                        del self.owner_sessions[session.owner]

                logger.info("session_removed", session_id=session_id)

    def _cleanup_worker(self) -> None:
        """Background worker to clean expired sessions"""

        while True:
            try:
                time.sleep(60)  # Check every minute

                expired = []
                oversized = []

                with self.lock:
                    for session_id, session in list(self.sessions.items()):
                        if session.is_expired():
                            expired.append(session_id)
                        elif session.is_over_limit():
                            oversized.append(session_id)

                # Remove expired
                for session_id in expired:
                    self._remove_session(session_id)

                # Log oversized (but don't remove - let owner handle)
                for session_id in oversized:
                    logger.warning(
                        "session_oversized",
                        session_id=session_id
                    )

                if expired:
                    logger.info(
                        "cleanup_complete",
                        expired_count=len(expired),
                        oversized_count=len(oversized)
                    )

            except Exception as e:
                logger.error("cleanup_error", error=str(e))

    def get_stats(self) -> Dict[str, Any]:
        """Get session manager statistics"""

        with self.lock:
            total_size = sum(
                session.size_bytes()
                for session in self.sessions.values()
            )

            return {
                "active_sessions": len(self.sessions),
                "max_sessions": self.max_sessions,
                "total_size_kb": total_size / 1024,
                "unique_owners": len(self.owner_sessions),
                "oldest_session": min(
                    (s.created_at for s in self.sessions.values()),
                    default=None
                )
            }


class SessionProtocol:
    """
    Protocol for session management commands
    Provides explicit control as requested in critique
    """

    def __init__(self, manager: SessionManager):
        self.manager = manager

    def execute_command(self, command: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute session management command"""

        commands = {
            "create": self._create,
            "reset": self._reset,
            "extend": self._extend,
            "list": self._list,
            "snapshot": self._snapshot,
            "restore": self._restore,
            "stats": self._stats
        }

        handler = commands.get(command)
        if not handler:
            return {"error": f"Unknown command: {command}"}

        try:
            return handler(params)
        except Exception as e:
            logger.error(f"session_command_failed", command=command, error=str(e))
            return {"error": str(e)}

    def _create(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create new session"""
        session_id = self.manager.create_session(
            owner=params.get("owner"),
            ttl=params.get("ttl", 3600)
        )
        return {"session_id": session_id, "status": "created"}

    def _reset(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Reset session context"""
        session_id = params.get("session_id")
        if not session_id:
            return {"error": "session_id required"}

        success = self.manager.reset_session(session_id)
        return {"status": "reset" if success else "not_found"}

    def _extend(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Extend session TTL"""
        session_id = params.get("session_id")
        additional_ttl = params.get("ttl", 3600)

        if not session_id:
            return {"error": "session_id required"}

        success = self.manager.extend_session(session_id, additional_ttl)
        return {"status": "extended" if success else "not_found"}

    def _list(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List active sessions"""
        sessions = self.manager.list_sessions(owner=params.get("owner"))
        return {"sessions": sessions, "count": len(sessions)}

    def _snapshot(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create session snapshot"""
        session_id = params.get("session_id")
        if not session_id:
            return {"error": "session_id required"}

        snapshot = self.manager.snapshot_session(session_id)
        return {"snapshot": snapshot} if snapshot else {"error": "session not found"}

    def _restore(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Restore session from snapshot"""
        snapshot = params.get("snapshot")
        if not snapshot:
            return {"error": "snapshot required"}

        session_id = self.manager.restore_session(snapshot)
        return {"session_id": session_id, "status": "restored"}

    def _stats(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get session statistics"""
        return self.manager.get_stats()