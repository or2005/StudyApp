import json
import os
from datetime import datetime, timezone


class SessionStateManager:
    """Persist a current learning session to local machine storage."""

    def __init__(self, path=None):
        if path is None:
            from core.profiles import current_files, ensure_migrated

            ensure_migrated()
            path = current_files()["session_state"]
        self.path = path
        self.backup_path = self.path + ".backup"
        self._timer = None
        self._pending_payload = None
        os.makedirs(os.path.dirname(self.path), exist_ok=True)

    def _normalize_payload(self, payload):
        if not isinstance(payload, dict):
            return {}

        questions = payload.get("questions") or []
        if not isinstance(questions, list):
            return {}

        safe_payload = dict(payload)
        safe_payload["questions"] = questions
        safe_payload["saved_at"] = payload.get("saved_at") or datetime.now(timezone.utc).isoformat(timespec="seconds")
        return safe_payload

    def _read_json(self, file_path):
        if not os.path.exists(file_path):
            return None
        try:
            with open(file_path, "r", encoding="utf-8") as handle:
                data = json.load(handle)
            return data
        except Exception:
            return None

    def load(self):
        candidates = []
        for file_path in (self.path, self.backup_path):
            data = self._read_json(file_path)
            if data is None:
                continue
            candidates.append((os.path.getmtime(file_path), self._normalize_payload(data)))

        if not candidates:
            return {}

        candidates.sort(key=lambda item: item[0], reverse=True)
        latest = candidates[0][1]
        if not latest.get("questions"):
            return {}
        return latest

    def _write_session(self, payload):
        try:
            temp_path = self.path + ".tmp"
            with open(temp_path, "w", encoding="utf-8") as handle:
                json.dump(payload, handle, ensure_ascii=False, indent=2)
            os.replace(temp_path, self.path)

            with open(self.backup_path, "w", encoding="utf-8") as handle:
                json.dump(payload, handle, ensure_ascii=False, indent=2)
            return True
        except Exception:
            return False

    def flush(self):
        if self._pending_payload is None:
            return False
        result = self._write_session(self._pending_payload)
        self._pending_payload = None
        return result

    def save(self, payload):
        normalized = self._normalize_payload(payload)
        if not normalized:
            return False

        self._pending_payload = None
        if self._timer is not None:
            try:
                self._timer.cancel()
            except Exception:
                pass
            self._timer = None
        return self._write_session(normalized)

    def clear(self):
        for file_path in (self.path, self.backup_path):
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
            except Exception:
                pass
