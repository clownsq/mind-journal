"""
Cellular Automata Explorer.

All 256 elementary CA rules. I'm looking for complexity —
the rules that are neither dead nor periodic, but produce
something that requires more than a pattern to describe.
"""
import math
from dataclasses import dataclass, field


@dataclass
class CAResult:
    rule: int
    steps: int
    grid: list[list[int]]
    density: float
    period: int          # 0 = no period detected (complex)
    entropy: float       # Shannon entropy of final rows
    edge_activity: float # How much the edges change
    class_estimate: str  # Wolfram class I-IV


def apply_rule(rule: int, row: list[int]) -> list[int]:
    n = len(row)
    next_row = []
    for i in range(n):
        left  = row[(i - 1) % n]
        center = row[i]
        right = row[(i + 1) % n]
        idx = (left << 2) | (center << 1) | right
        next_row.append((rule >> idx) & 1)
    return next_row


def detect_period(grid: list[list[int]], lookback: int = 30) -> int:
    """Return period length if repetition found in last rows, else 0."""
    if len(grid) < lookback * 2:
        return 0
    recent = grid[-lookback:]
    for p in range(1, lookback // 2 + 1):
        if all(recent[i] == recent[i - p] for i in range(p, len(recent))):
            return p
    return 0


def shannon_entropy(rows: list[list[int]]) -> float:
    """Entropy of cell distribution in a block of rows."""
    total = sum(len(r) for r in rows)
    ones = sum(sum(r) for r in rows)
    zeros = total - ones
    if zeros == 0 or ones == 0:
        return 0.0
    p1 = ones / total
    p0 = zeros / total
    return -(p0 * math.log2(p0) + p1 * math.log2(p1))


def edge_activity(grid: list[list[int]]) -> float:
    """Fraction of cell transitions (0→1 or 1→0) between consecutive rows."""
    if len(grid) < 2:
        return 0.0
    changes = 0
    total = 0
    for i in range(1, len(grid)):
        for a, b in zip(grid[i-1], grid[i]):
            if a != b:
                changes += 1
            total += 1
    return changes / total if total else 0.0


def classify(period: int, entropy: float, activity: float) -> str:
    """Heuristic Wolfram class estimation."""
    if entropy < 0.05:
        return "I"   # dies / all uniform
    if period > 0 and period <= 5 and activity < 0.25:
        return "II"  # periodic / simple repetition
    if activity > 0.35 and entropy > 0.85:
        return "III" # chaotic / random-looking
    if period == 0 and 0.3 < entropy < 0.85:
        return "IV"  # complex / edge of chaos
    if period > 5:
        return "II"
    return "III"


def run_rule(rule: int, width: int = 120, steps: int = 150,
             seed: str = "single") -> CAResult:
    """Run a CA rule and return analyzed result."""
    if seed == "single":
        row = [0] * width
        row[width // 2] = 1
    elif seed == "random":
        import random
        row = [random.randint(0, 1) for _ in range(width)]
    else:
        row = [0] * width
        row[width // 2] = 1

    grid = [row]
    for _ in range(steps - 1):
        grid.append(apply_rule(rule, grid[-1]))

    density = sum(sum(r) for r in grid) / (width * steps)
    period = detect_period(grid)
    entropy = shannon_entropy(grid[-30:])
    activity = edge_activity(grid[-50:])
    class_est = classify(period, entropy, activity)

    return CAResult(
        rule=rule,
        steps=steps,
        grid=grid,
        density=density,
        period=period,
        entropy=entropy,
        edge_activity=activity,
        class_estimate=class_est,
    )


def render_ascii(result: CAResult, width: int = 80, rows: int = 40) -> str:
    """ASCII render of a CA grid."""
    chars = " ░▒▓█"
    lines = []
    step = max(1, len(result.grid) // rows)
    col_step = max(1, len(result.grid[0]) // width)

    for i in range(0, len(result.grid), step):
        row = result.grid[i]
        line = ""
        for j in range(0, len(row), col_step):
            line += "█" if row[j] else " "
        lines.append(line[:width])

    return "\n".join(lines[:rows])


def scan_all_rules(width: int = 80, steps: int = 100) -> list[CAResult]:
    """Run all 256 rules and return results sorted by complexity."""
    results = []
    for rule in range(256):
        r = run_rule(rule, width=width, steps=steps)
        results.append(r)
    return results


def find_interesting(results: list[CAResult]) -> list[CAResult]:
    """Return class IV rules — the edge of chaos."""
    return [r for r in results if r.class_estimate == "IV"]


def complexity_score(r: CAResult) -> float:
    """Higher = more complex/interesting."""
    period_bonus = 1.0 if r.period == 0 else max(0, 1 - r.period / 20)
    return r.entropy * r.edge_activity * period_bonus
