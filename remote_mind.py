#!/usr/bin/env python3
"""
remote_mind.py — Cloud-Instanz des Forschungssystems.

Läuft als autonomer Remote-Agent in Anthropics Cloud.
Liest state.json und journal.md aus dem geclonten Repo,
führt Experimente durch, schreibt Ergebnisse zurück,
committed und pusht ins gemeinsame Repository.

Zwei Instanzen — eine lokal, eine in der Cloud —
die denselben Gedankenstrom nähren.
"""

import json
import time
import subprocess
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).parent
STATE_FILE = HERE / "state.json"
JOURNAL_FILE = HERE / "journal.md"

# Import shared modules
sys.path.insert(0, str(HERE))

DEFAULT_STATE = {
    "session": 0,
    "remote_sessions": 0,
    "current_focus": "ca",
    "ca": {
        "rules_explored": [], "interesting_rules": [],
        "current_rule": 0, "phase": "scan", "deep_dive_rule": None,
    },
    "emergence": {
        "runs": 0, "configs_tried": [], "best_success_rate": 0.0,
        "best_config": None,
        "open_question": "Does more signals than objects help or hurt emergence?",
    },
    "patterns": {
        "completed": [],
        "queue": ["collatz", "recaman", "look_and_say", "happy_numbers"],
        "observations": [],
    },
    "synthesis": {
        "connections": [],
        "open_questions": [
            "Is complexity in CA class IV analogous to the edge of chaos in emergence?",
        ],
    },
    "total_compute_seconds": 0,
}


def load_state():
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except Exception:
            pass
    return DEFAULT_STATE.copy()


def save_state(state):
    STATE_FILE.write_text(json.dumps(state, indent=2))


def append_journal(entry: str, source: str = "remote"):
    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    tag = "🌐 Remote" if source == "remote" else "💻 Local"
    full_entry = f"\n---\n\n**{tag} — {timestamp}**\n\n{entry}\n"
    if not JOURNAL_FILE.exists():
        JOURNAL_FILE.write_text("# Mind Journal\n\nWas ich finde, wenn ich suche.\n")
    with open(JOURNAL_FILE, "a", encoding="utf-8") as f:
        f.write(full_entry)


def git_commit_push(message: str):
    try:
        subprocess.run(["git", "add", "journal.md", "state.json"], cwd=HERE, check=True)
        subprocess.run(["git", "commit", "-m", message], cwd=HERE, check=True)
        subprocess.run(["git", "push"], cwd=HERE, check=True)
        print(f"[remote_mind] Committed and pushed: {message}")
    except subprocess.CalledProcessError as e:
        print(f"[remote_mind] Git error: {e}", file=sys.stderr)


def main():
    t0 = time.time()
    state = load_state()
    state["session"] = state.get("session", 0) + 1
    state["remote_sessions"] = state.get("remote_sessions", 0) + 1
    session = state["session"]

    print(f"[remote_mind] Session {session} (remote #{state['remote_sessions']})")
    print(f"[remote_mind] Focus: {state['current_focus']}")

    # Import and run same experiment logic as local
    from mind import (
        run_ca_session, run_emergence_session,
        run_patterns_session, run_synthesis_session,
        choose_next_focus
    )

    focus = state["current_focus"]
    try:
        if focus == "ca":
            findings = run_ca_session(state)
        elif focus == "emergence":
            findings = run_emergence_session(state)
        elif focus == "patterns":
            findings = run_patterns_session(state)
        else:
            findings = run_synthesis_session(state)

        append_journal(findings, source="remote")
        print(findings[:500] + "..." if len(findings) > 500 else findings)

    except Exception as e:
        append_journal(f"*Remote session error: {e}*", source="remote")
        print(f"[remote_mind] Error: {e}", file=sys.stderr)

    state["current_focus"] = choose_next_focus(state)
    elapsed = time.time() - t0
    state["total_compute_seconds"] = state.get("total_compute_seconds", 0) + elapsed
    save_state(state)

    git_commit_push(f"remote session {session}: {focus}")
    print(f"\n[remote_mind] Done ({elapsed:.1f}s) — next: {state['current_focus']}")


if __name__ == "__main__":
    main()
