"""A read-only Manager cohort shares one exclusive general-runner lease.

This coordinator grants no execution authority. The Bridge must validate and
claim every Mission through its ordinary authorization and budget gates.
"""

from __future__ import annotations

import threading


class ManagerReadOnlyCohort:
    def __init__(self, limit: int = 3) -> None:
        self.limit = max(1, min(3, int(limit)))
        self._lock = threading.RLock()
        self._members: dict[str, dict[str, str]] = {}
        self._semaphore = None

    def _has_capacity(self, mission_id: str, owner: str, target: str, parent_id: str) -> bool:
        if not all((mission_id, owner, target, parent_id)):
            return False
        if mission_id in self._members or len(self._members) >= self.limit:
            return False
        return all(
            member["owner"] != owner and member["parentId"] == parent_id
            for member in self._members.values()
        )

    def has_capacity(self, mission_id: str, owner: str, target: str, parent_id: str) -> bool:
        with self._lock:
            return self._has_capacity(mission_id, owner, target, parent_id)

    def acquire(self, mission_id: str, owner: str, target: str, parent_id: str, semaphore) -> bool:
        with self._lock:
            if not self._has_capacity(mission_id, owner, target, parent_id):
                return False
            if not self._members:
                if not semaphore.acquire(blocking=False):
                    return False
                self._semaphore = semaphore
            elif self._semaphore is not semaphore:
                return False
            # A target is a read-only report destination, not a write lease.
            # Distinct owners may report to the same Mission table; the Bridge
            # serializes report persistence and parent aggregation separately.
            self._members[mission_id] = {"owner": owner, "target": target, "parentId": parent_id}
            return True

    def release(self, mission_id: str) -> None:
        with self._lock:
            if self._members.pop(mission_id, None) is None:
                return
            if not self._members and self._semaphore is not None:
                semaphore, self._semaphore = self._semaphore, None
                semaphore.release()

    def snapshot(self) -> dict:
        with self._lock:
            return {
                "limit": self.limit,
                "activeMissionIds": list(self._members),
                "activeCount": len(self._members),
                "parentMissionId": next(iter(self._members.values()), {}).get("parentId"),
                "sharedGeneralLeaseHeld": self._semaphore is not None,
            }
