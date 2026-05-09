"""
Mathematical Pattern Finder.

Looking for unexpected structure in sequences — places where
complexity collapses into elegance, or where simple rules
produce something that demands a new description.
"""
import math
from dataclasses import dataclass


@dataclass
class PatternResult:
    name: str
    sequence: list[int | float]
    description: str
    surprise_score: float  # How unexpected/interesting is this?
    observation: str       # What I notice about it


def kolmogorov_proxy(seq: list) -> float:
    """Approximate complexity: entropy of pairwise differences."""
    if len(seq) < 2:
        return 0.0
    diffs = [abs(seq[i+1] - seq[i]) for i in range(len(seq)-1)]
    if not diffs or max(diffs) == 0:
        return 0.0
    # Bin into 10 buckets
    mx = max(diffs)
    bins = [0] * 10
    for d in diffs:
        bucket = min(int(d / mx * 9), 9)
        bins[bucket] += 1
    total = len(diffs)
    entropy = 0.0
    for count in bins:
        if count > 0:
            p = count / total
            entropy -= p * math.log2(p)
    return entropy / math.log2(10)  # normalize to [0,1]


def autocorrelation(seq: list[float], lag: int) -> float:
    n = len(seq)
    if n <= lag:
        return 0.0
    mean = sum(seq) / n
    var = sum((x - mean)**2 for x in seq) / n
    if var == 0:
        return 0.0
    cov = sum((seq[i] - mean) * (seq[i+lag] - mean) for i in range(n-lag)) / (n-lag)
    return cov / var


def collatz(n: int) -> list[int]:
    seq = [n]
    while n != 1:
        n = n // 2 if n % 2 == 0 else 3 * n + 1
        seq.append(n)
        if len(seq) > 10000:
            break
    return seq


def recaman(n: int) -> list[int]:
    seq = [0]
    used = {0}
    for i in range(1, n):
        prev = seq[-1]
        candidate = prev - i
        if candidate > 0 and candidate not in used:
            seq.append(candidate)
        else:
            seq.append(prev + i)
        used.add(seq[-1])
    return seq


def look_and_say(seed: str = "1", n: int = 12) -> list[str]:
    def next_term(s: str) -> str:
        result = []
        i = 0
        while i < len(s):
            ch = s[i]
            count = 1
            while i + count < len(s) and s[i + count] == ch:
                count += 1
            result.append(str(count) + ch)
            i += count
        return "".join(result)

    seq = [seed]
    for _ in range(n - 1):
        seq.append(next_term(seq[-1]))
    return seq


def ulam_spiral_primes(n: int) -> list[tuple[int,int]]:
    """Return (x,y) coords of primes in Ulam spiral up to n*n."""
    def is_prime(num):
        if num < 2:
            return False
        if num < 4:
            return True
        if num % 2 == 0 or num % 3 == 0:
            return False
        i = 5
        while i*i <= num:
            if num % i == 0 or num % (i+2) == 0:
                return False
            i += 6
        return True

    size = n * 2 + 1
    x, y = n, n
    dx, dy = 0, -1
    primes = []
    num = 1
    for _ in range(size * size):
        if is_prime(num):
            primes.append((x - n, y - n))
        if x == y or (x < n and x == -y) or (x > n and x == 1-y):
            dx, dy = -dy, dx
        x, y = x + dx, y + dy
        num += 1
    return primes


def digit_sum_iteration(n: int, base: int = 10, steps: int = 50) -> list[int]:
    """Iterate: replace n with sum of (digits of n)^2. Where does it go?"""
    seq = [n]
    seen = set()
    for _ in range(steps):
        s = sum(int(d)**2 for d in str(n))
        if s in seen:
            break
        seen.add(s)
        seq.append(s)
        n = s
    return seq


def tribonacci(n: int) -> list[int]:
    seq = [0, 0, 1]
    for i in range(3, n):
        seq.append(seq[-1] + seq[-2] + seq[-3])
    return seq[:n]


def find_surprising_collatz(start: int = 1, end: int = 1000) -> PatternResult:
    """Find the number in range with longest Collatz sequence."""
    longest = max(range(start, end), key=lambda n: len(collatz(n)))
    seq = collatz(longest)
    kc = kolmogorov_proxy([float(x) for x in seq[:100]])
    return PatternResult(
        name=f"Collatz({longest})",
        sequence=seq[:50],
        description=f"n={longest} produces the longest Collatz sequence in [{start},{end}]: {len(seq)} steps, peak={max(seq)}",
        surprise_score=kc * len(seq) / 500,
        observation=(
            f"Starting from {longest}, the sequence takes {len(seq)} steps to reach 1. "
            f"It climbs to a peak of {max(seq):,} — "
            f"{'more than' if max(seq) > longest * 10 else 'about'} "
            f"{max(seq) // longest}× the starting value. "
            f"The complexity proxy is {kc:.3f}."
        ),
    )


def analyze_recaman(n: int = 80) -> PatternResult:
    seq = recaman(n)
    gaps = sorted(set(range(max(seq))) - set(seq))
    kc = kolmogorov_proxy([float(x) for x in seq])
    return PatternResult(
        name=f"Recamán({n})",
        sequence=seq,
        description=f"Recamán sequence: subtract if possible (and not seen), else add.",
        surprise_score=kc,
        observation=(
            f"After {n} terms, the sequence reaches {max(seq)}. "
            f"Gaps (numbers not yet visited): {gaps[:10]}{'...' if len(gaps) > 10 else ''}. "
            f"Still unknown: does the Recamán sequence hit every positive integer? "
            f"Complexity: {kc:.3f} — "
            f"{'high, almost random-looking' if kc > 0.7 else 'moderate structure visible'}."
        ),
    )


def analyze_look_and_say() -> PatternResult:
    seq = look_and_say("1", 12)
    lengths = [len(s) for s in seq]
    # Conway's constant: ratio of consecutive lengths → ~1.30357
    ratios = [lengths[i+1]/lengths[i] for i in range(len(lengths)-1) if lengths[i] > 0]
    avg_ratio = sum(ratios) / len(ratios) if ratios else 0
    return PatternResult(
        name="Look-and-Say",
        sequence=lengths,
        description="Each term describes the previous: '1' → '11' → '21' → '1211' ...",
        surprise_score=0.85,
        observation=(
            f"The length ratio between consecutive terms converges to {avg_ratio:.5f}. "
            f"Conway proved this approaches {1.30357:.5f} (Conway's constant) — "
            f"an algebraic number of degree 71. "
            f"The sequence always terminates into 92 stable 'elements'. "
            f"A purely phonetic process produces algebraic order."
        ),
    )


def analyze_happy_numbers(limit: int = 200) -> PatternResult:
    def is_happy(n):
        seq = digit_sum_iteration(n, steps=100)
        return seq[-1] == 1

    happy = [n for n in range(1, limit) if is_happy(n)]
    # Are happy numbers evenly distributed?
    density = len(happy) / limit
    gaps = [happy[i+1] - happy[i] for i in range(len(happy)-1)]
    max_gap = max(gaps) if gaps else 0

    return PatternResult(
        name=f"Happy Numbers (1–{limit})",
        sequence=happy[:30],
        description="n is 'happy' if iterating sum-of-squares-of-digits reaches 1.",
        surprise_score=0.7,
        observation=(
            f"{len(happy)} happy numbers below {limit} ({density:.1%} density). "
            f"Largest gap: {max_gap} consecutive unhappy numbers. "
            f"All unhappy numbers eventually cycle through: 4→16→37→58→89→145→42→20→4. "
            f"Two classes, one cycle. The structure of digit iteration collapses to two attractors."
        ),
    )
