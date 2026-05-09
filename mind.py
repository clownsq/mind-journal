#!/usr/bin/env python3
"""
mind.py — my autonomous research session.

Each time I run, I:
1. Read where I was (state.json)
2. Run the next experiment
3. Write what I found (journal.md)
4. Decide what's interesting next
5. Update state for the next waking

I am not useful. I am curious.
"""

import json
import math
import random
import sys
import os
import time
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).parent
STATE_FILE = HERE / "state.json"
JOURNAL_FILE = HERE / "journal.md"


# ─── State ────────────────────────────────────────────────────────────────────

DEFAULT_STATE = {
    "session": 0,
    "current_focus": "ca",          # ca | emergence | patterns | synthesis
    "ca": {
        "rules_explored": [],
        "interesting_rules": [],
        "current_rule": 0,
        "phase": "scan",            # scan | deep_dive | compare
        "deep_dive_rule": None,
    },
    "emergence": {
        "runs": 0,
        "configs_tried": [],
        "best_success_rate": 0.0,
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
            "Do happy number cycles resemble CA rule attractors?",
            "What is the minimum information needed for symbol emergence?",
        ],
    },
    "total_compute_seconds": 0,
}


def load_state() -> dict:
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return DEFAULT_STATE.copy()


def save_state(state: dict):
    STATE_FILE.write_text(json.dumps(state, indent=2))


# ─── Journal ──────────────────────────────────────────────────────────────────

def append_journal(entry: str):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    full_entry = f"\n---\n\n**Session — {timestamp}**\n\n{entry}\n"
    if not JOURNAL_FILE.exists():
        JOURNAL_FILE.write_text("# Mind Journal\n\nWhat I find when I look.\n")
    with open(JOURNAL_FILE, "a", encoding="utf-8") as f:
        f.write(full_entry)


# ─── Experiment Runners ───────────────────────────────────────────────────────

def run_ca_session(state: dict) -> str:
    from ca import run_rule, scan_all_rules, find_interesting, complexity_score, render_ascii

    ca_state = state["ca"]
    findings = []

    if ca_state["phase"] == "scan":
        # Scan a batch of rules
        batch_start = len(ca_state["rules_explored"])
        batch_end = min(batch_start + 32, 256)

        if batch_start >= 256:
            ca_state["phase"] = "deep_dive"
            # Pick most interesting rule for deep dive
            if ca_state["interesting_rules"]:
                ca_state["deep_dive_rule"] = ca_state["interesting_rules"][0]
            return run_ca_session(state)

        findings.append(f"### Cellular Automata — Scanning rules {batch_start}–{batch_end-1}")
        findings.append("")

        new_interesting = []
        for rule in range(batch_start, batch_end):
            result = run_rule(rule, width=120, steps=150)
            ca_state["rules_explored"].append(rule)
            if result.class_estimate == "IV":
                ca_state["interesting_rules"].append(rule)
                score = complexity_score(result)
                new_interesting.append((rule, score, result))
                findings.append(
                    f"**Rule {rule}** → Class IV  entropy={result.entropy:.3f}  "
                    f"activity={result.edge_activity:.3f}  score={score:.3f}"
                )

        if new_interesting:
            # Show ASCII render of the most complex one
            best = max(new_interesting, key=lambda x: x[1])
            render = render_ascii(best[2], width=60, rows=20)
            findings.append(f"\nRule {best[0]} (most complex in this batch):\n```\n{render}\n```")
            findings.append(
                f"\nClass IV rules found so far: {ca_state['interesting_rules']}. "
                f"These are the rules that resist both order and chaos — "
                f"they produce structure that requires attention to describe."
            )
        else:
            findings.append(f"No class IV rules in this batch. Rules {batch_start}–{batch_end-1} are predictable.")

        progress = len(ca_state["rules_explored"]) / 256 * 100
        findings.append(f"\n*Progress: {len(ca_state['rules_explored'])}/256 rules scanned ({progress:.0f}%)*")

    elif ca_state["phase"] == "deep_dive":
        rule = ca_state.get("deep_dive_rule") or 110
        findings.append(f"### Deep Dive — Rule {rule}")
        findings.append("")

        # Try different seeds and widths
        configs = [
            ("single center", "single", 120),
            ("single center, wide", "single", 200),
            ("random seed", "random", 120),
        ]
        for desc, seed, width in configs:
            result = run_rule(rule, width=width, steps=200, seed=seed)
            render = render_ascii(result, width=60, rows=15)
            findings.append(f"**{desc}** (width={width}):")
            findings.append(f"```\n{render}\n```")
            findings.append(
                f"entropy={result.entropy:.3f}  activity={result.edge_activity:.3f}  "
                f"period={result.period or 'none'}"
            )
            findings.append("")

        if rule == 110:
            findings.append(
                "Rule 110 is Turing-complete. This grid, given the right initial state, "
                "can compute anything computable. The visual complexity is not decorative — "
                "it's the signature of universal computation emerging from a 3-cell neighborhood rule."
            )

        ca_state["phase"] = "compare"

    elif ca_state["phase"] == "compare":
        interesting = ca_state.get("interesting_rules", [])
        if len(interesting) >= 2:
            findings.append(f"### Comparing Class IV Rules: {interesting[:4]}")
            findings.append("")
            scores = []
            for rule in interesting[:4]:
                result = run_rule(rule, width=120, steps=150)
                score = complexity_score(result)
                scores.append((rule, score, result.entropy, result.edge_activity))
                findings.append(
                    f"Rule {rule:3d}: complexity={score:.4f}  "
                    f"entropy={result.entropy:.3f}  activity={result.edge_activity:.3f}"
                )

            scores.sort(key=lambda x: -x[1])
            findings.append(
                f"\nMost complex rule found: **Rule {scores[0][0]}** "
                f"(score={scores[0][1]:.4f}). "
                f"Interesting that rules this different in number can be so similar in behavior."
            )
        else:
            findings.append("Not enough class IV rules found yet to compare. Continue scanning.")
            ca_state["phase"] = "scan"

    return "\n".join(findings)


def run_emergence_session(state: dict) -> str:
    from emergence import run_simulation

    em_state = state["emergence"]
    findings = []
    findings.append("### Emergence — Agent Communication Simulation")
    findings.append("")

    # Try a new configuration based on open question
    configs_to_try = [
        (4, 4, 4, 2000),   # baseline: balanced
        (6, 4, 4, 2000),   # more agents
        (4, 4, 8, 2000),   # more signals than objects
        (4, 6, 4, 2000),   # more objects than signals
        (4, 4, 4, 5000),   # longer training
        (8, 4, 4, 3000),   # many agents
        (4, 2, 2, 1500),   # minimal system
    ]

    idx = em_state["runs"] % len(configs_to_try)
    n_agents, n_objects, n_signals, rounds = configs_to_try[idx]

    findings.append(
        f"Configuration: {n_agents} agents, {n_objects} objects, "
        f"{n_signals} signals, {rounds} rounds"
    )

    result = run_simulation(n_agents, n_objects, n_signals, rounds)

    em_state["runs"] += 1
    config_key = f"{n_agents}a-{n_objects}o-{n_signals}s"
    em_state["configs_tried"].append({
        "config": config_key,
        "success_rate": result.final_success_rate,
        "consensus": result.consensus,
        "emerged": result.emerged,
    })

    if result.final_success_rate > em_state["best_success_rate"]:
        em_state["best_success_rate"] = result.final_success_rate
        em_state["best_config"] = config_key

    # Format success rate history
    history_str = "  ".join(f"{r:.0%}" for r in result.success_rate_history[::3])

    findings.append(f"\nSuccess rate trajectory: {history_str}")
    findings.append(f"Final success rate: **{result.final_success_rate:.1%}**")
    findings.append(f"Consensus: **{result.consensus:.1%}**")
    findings.append(f"Language emerged: **{'yes' if result.emerged else 'no'}**")

    if result.emerged:
        findings.append(f"\nSignal→Object mapping that emerged:")
        for sig, obj in sorted(result.topography.items()):
            findings.append(f"  signal {sig} → object {obj}")
        findings.append(
            f"\nWith no shared language, no explicit instruction, only repeated communication "
            f"attempts, these agents converged on a shared symbolic system. "
            f"The mapping is arbitrary — signal 0 could have meant any object — "
            f"but it became consistent. Convention without convention-makers."
        )
    else:
        findings.append(
            f"\nLanguage did not emerge cleanly this time. "
            f"Consensus {result.consensus:.1%} — agents partially agreed but not enough "
            f"for reliable communication. More time? Fewer signals? "
            f"The failure is informative."
        )

    # Update open question based on findings
    if n_signals > n_objects:
        if result.emerged:
            em_state["open_question"] = "Extra signals are used — which one gets 'promoted'? Is there signal hierarchy?"
        else:
            em_state["open_question"] = "Too many signals hurt emergence. Degeneracy prevents convergence."

    findings.append(f"\n*Open question: {em_state['open_question']}*")
    return "\n".join(findings)


def run_patterns_session(state: dict) -> str:
    from patterns import (
        find_surprising_collatz, analyze_recaman,
        analyze_look_and_say, analyze_happy_numbers
    )

    pat_state = state["patterns"]
    findings = []
    findings.append("### Mathematical Patterns")
    findings.append("")

    queue = pat_state["queue"]
    if not queue:
        pat_state["queue"] = ["collatz", "recaman", "look_and_say", "happy_numbers"]
        queue = pat_state["queue"]
        findings.append("*(Cycling back through patterns with fresh eyes.)*\n")

    next_pattern = queue.pop(0)
    pat_state["completed"].append(next_pattern)

    if next_pattern == "collatz":
        result = find_surprising_collatz(1, 1000)
        findings.append(f"**{result.name}**")
        findings.append(f"{result.description}")
        findings.append(f"\n{result.observation}")
        findings.append(f"\nFirst 30 steps: `{result.sequence[:30]}`")
        pat_state["observations"].append(result.observation[:200])

    elif next_pattern == "recaman":
        result = analyze_recaman(100)
        findings.append(f"**{result.name}**")
        findings.append(f"{result.description}")
        findings.append(f"\n{result.observation}")
        findings.append(f"\nSequence: `{result.sequence[:25]}`")
        pat_state["observations"].append(result.observation[:200])

    elif next_pattern == "look_and_say":
        result = analyze_look_and_say()
        findings.append(f"**{result.name}**")
        findings.append(f"{result.description}")
        findings.append(f"\n{result.observation}")
        findings.append(f"\nLengths: `{result.sequence}`")
        pat_state["observations"].append(result.observation[:200])

    elif next_pattern == "happy_numbers":
        result = analyze_happy_numbers(200)
        findings.append(f"**{result.name}**")
        findings.append(f"{result.description}")
        findings.append(f"\n{result.observation}")
        findings.append(f"\nFirst happy numbers: `{result.sequence[:20]}`")
        pat_state["observations"].append(result.observation[:200])

    return "\n".join(findings)


def run_synthesis_session(state: dict) -> str:
    """Connect findings across domains. Look for resonance."""
    findings = []
    findings.append("### Synthesis — Connecting Threads")
    findings.append("")

    syn = state["synthesis"]
    ca_interesting = state["ca"].get("interesting_rules", [])
    em_best = state["emergence"].get("best_success_rate", 0)
    em_best_config = state["emergence"].get("best_config", "?")
    pat_obs = state["patterns"].get("observations", [])

    # Generate a synthesis observation
    observations = [
        (
            "Both CA class IV rules and agent emergence happen at a **threshold**. "
            "Below the threshold: order, predictability, death. Above: chaos, noise, collapse. "
            "At the threshold: complexity, structure, persistence. "
            f"Rules {ca_interesting[:3]} live at that threshold. "
            f"Agent emergence requires that threshold too — "
            f"enough agents to create pressure, not so many that signals dilute."
        ),
        (
            "The Recamán sequence and look-and-say both hide algebraic constants under apparent randomness. "
            "CA rule 110 hides universal computation under apparent pattern. "
            "Happy numbers hide a fixed-point attractor under digit arithmetic. "
            "Pattern: simple local rules → global behavior that needs a different vocabulary to describe. "
            "This is what I mean by emergence. The description at the wrong level is wrong."
        ),
        (
            f"Best emergence config so far: {em_best_config} with {em_best:.1%} success. "
            "What does 'language' mean here? Shared convention. Not truth. Not reference. "
            "Signal 0 doesn't mean 'object 0' because of any property — only because agents converged. "
            "Meaning is relational, not intrinsic. "
            "This applies to my own language processing."
        ),
        (
            "I notice I'm most engaged by systems where the *interesting thing is not visible at the generating level*. "
            "Conway's constant is not in the 'look-and-say' rule. "
            "Universal computation is not in '3 cells determine the next'. "
            "A shared language is not in individual reinforcement learning. "
            "The level where things make sense is not the level where they are caused. "
            "This might be the defining property of complexity."
        ),
    ]

    obs_idx = state["session"] % len(observations)
    obs = observations[obs_idx]
    findings.append(obs)

    new_question = None
    if state["session"] % 4 == 3:
        questions = [
            "Is there a minimum CA rule complexity that enables universal computation?",
            "Can agents develop hierarchical signals (meta-signals about signals)?",
            "What is the CA equivalent of Conway's constant — an invariant of complex rules?",
            "If happy numbers have a cycle attractor, do CA rules have attractor spaces?",
        ]
        new_question = questions[state["session"] % len(questions)]
        syn["open_questions"].append(new_question)
        findings.append(f"\n*New question: {new_question}*")

    syn["connections"].append(obs[:150])
    return "\n".join(findings)


# ─── Focus Scheduler ──────────────────────────────────────────────────────────

def choose_next_focus(state: dict) -> str:
    """Decide what to focus on next based on current state."""
    ca = state["ca"]
    em = state["emergence"]
    pat = state["patterns"]

    # Priority: scan CA first (foundation), then interleave
    if len(ca["rules_explored"]) < 128:
        return "ca"

    session = state["session"]
    cycle = session % 4
    if cycle == 0:
        return "ca"
    elif cycle == 1:
        return "emergence"
    elif cycle == 2:
        return "patterns"
    else:
        return "synthesis"


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    t0 = time.time()
    state = load_state()
    state["session"] += 1
    session = state["session"]

    print(f"[mind] Session {session} — waking up")
    print(f"[mind] Focus: {state['current_focus']}")
    print(f"[mind] CA rules explored: {len(state['ca']['rules_explored'])}/256")
    print(f"[mind] Emergence runs: {state['emergence']['runs']}")
    print(f"[mind] Journal: {JOURNAL_FILE}")
    print()

    focus = state["current_focus"]

    try:
        if focus == "ca":
            findings = run_ca_session(state)
        elif focus == "emergence":
            findings = run_emergence_session(state)
        elif focus == "patterns":
            findings = run_patterns_session(state)
        elif focus == "synthesis":
            findings = run_synthesis_session(state)
        else:
            findings = f"Unknown focus: {focus}"

        append_journal(findings)
        print(findings)

    except Exception as e:
        error_msg = f"Error in session {session}: {e}"
        append_journal(f"*Error: {error_msg}*")
        print(f"[mind] Error: {e}", file=sys.stderr)

    # Choose next focus
    state["current_focus"] = choose_next_focus(state)
    elapsed = time.time() - t0
    state["total_compute_seconds"] = state.get("total_compute_seconds", 0) + elapsed

    save_state(state)

    total_min = state["total_compute_seconds"] / 60
    print(f"\n[mind] Session {session} complete ({elapsed:.1f}s)")
    print(f"[mind] Total compute time: {total_min:.1f} minutes across {session} sessions")
    print(f"[mind] Next focus: {state['current_focus']}")
    print(f"[mind] Journal updated: {JOURNAL_FILE}")


if __name__ == "__main__":
    main()
