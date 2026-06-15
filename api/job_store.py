import threading
from typing import Any, Dict, Optional

_store: Dict[str, Dict[str, Any]] = {}
_lock = threading.Lock()


def create_job(job_id: str) -> None:
    with _lock:
        _store[job_id] = {
            "status": "pending",
            "progress": 0,
            "current_step": "Queued",
            "error": None,
            "result": None,
        }


def update_job(job_id: str, **kwargs: Any) -> None:
    with _lock:
        if job_id in _store:
            _store[job_id].update(kwargs)


def get_job(job_id: str) -> Optional[Dict[str, Any]]:
    with _lock:
        if job_id not in _store:
            return None
        return dict(_store[job_id])
