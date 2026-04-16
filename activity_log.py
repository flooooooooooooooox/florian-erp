import json
import os
from datetime import datetime

LOG_FILE = "activity_log.jsonl"


def log_activity(actor: str, action: str, target: str = "", details: dict | None = None) -> bool:
    entry = {
        "ts": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "actor": str(actor or "").strip() or "inconnu",
        "action": str(action or "").strip() or "action",
        "target": str(target or "").strip(),
        "details": details or {},
    }
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        return True
    except Exception:
        return False


def read_activity_logs(limit: int = 200) -> list:
    if not os.path.exists(LOG_FILE):
        return []
    rows = []
    try:
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    rows.append(json.loads(line))
                except Exception:
                    continue
    except Exception:
        return []
    rows.reverse()
    return rows[:limit]
