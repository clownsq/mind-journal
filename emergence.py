"""
Emergence Simulator.

Simple agents under communication pressure — do they develop
stable signal-meaning associations? This is a miniature version
of the question: how does symbol use become language?

Model: N agents, M objects, K signals.
Each agent has a policy: object → signal (speaker) and
signal → object guess (listener).
Reward: correct communication → reinforce both.
No shared initial knowledge. Only pressure: communicate or fail.
"""
import random
import math
from dataclasses import dataclass, field
from collections import defaultdict


@dataclass
class Agent:
    id: int
    n_objects: int
    n_signals: int
    # Speaker policy: P(signal | object)
    speaker: list[list[float]] = field(default_factory=list)
    # Listener policy: P(object | signal)
    listener: list[list[float]] = field(default_factory=list)

    def __post_init__(self):
        # Uniform initialization
        self.speaker = [
            [1.0 / self.n_signals] * self.n_signals
            for _ in range(self.n_objects)
        ]
        self.listener = [
            [1.0 / self.n_objects] * self.n_objects
            for _ in range(self.n_signals)
        ]

    def speak(self, obj: int) -> int:
        """Sample a signal for the given object."""
        probs = self.speaker[obj]
        r = random.random()
        cumulative = 0.0
        for i, p in enumerate(probs):
            cumulative += p
            if r <= cumulative:
                return i
        return len(probs) - 1

    def listen(self, signal: int) -> int:
        """Guess the object from the signal."""
        probs = self.listener[signal]
        return probs.index(max(probs))

    def reinforce_speaker(self, obj: int, signal: int, reward: float, lr: float = 0.1):
        """Increase P(signal|obj) by lr * reward."""
        probs = self.speaker[obj]
        probs[signal] += lr * reward
        total = sum(probs)
        self.speaker[obj] = [p / total for p in probs]

    def reinforce_listener(self, signal: int, obj: int, reward: float, lr: float = 0.1):
        probs = self.listener[signal]
        probs[obj] += lr * reward
        total = sum(probs)
        self.listener[signal] = [p / total for p in probs]


@dataclass
class EmergenceResult:
    n_agents: int
    n_objects: int
    n_signals: int
    rounds: int
    success_rate_history: list[float]
    final_success_rate: float
    topography: dict   # signal → dominant object across agents
    consensus: float   # 0=chaos, 1=full consensus
    entropy_history: list[float]
    emerged: bool


def measure_consensus(agents: list[Agent], n_objects: int, n_signals: int) -> tuple[float, dict]:
    """
    Consensus: do agents agree on what each signal means?
    Returns (consensus_score, topography).
    """
    # For each signal, find what each agent's listener thinks is dominant
    signal_votes: dict[int, list[int]] = defaultdict(list)
    for agent in agents:
        for sig in range(n_signals):
            dominant_obj = agent.listener[sig].index(max(agent.listener[sig]))
            signal_votes[sig].append(dominant_obj)

    # Consensus per signal = fraction of agents that agree on dominant object
    consensus_scores = []
    topography = {}
    for sig, votes in signal_votes.items():
        most_common = max(set(votes), key=votes.count)
        agreement = votes.count(most_common) / len(votes)
        consensus_scores.append(agreement)
        topography[sig] = most_common

    return sum(consensus_scores) / len(consensus_scores), topography


def policy_entropy(agent: Agent) -> float:
    """Average entropy of speaker policy — low = more decisive."""
    total_entropy = 0.0
    for obj_probs in agent.speaker:
        for p in obj_probs:
            if p > 0:
                total_entropy -= p * math.log2(p)
    return total_entropy / agent.n_objects


def run_simulation(
    n_agents: int = 6,
    n_objects: int = 4,
    n_signals: int = 4,
    rounds: int = 3000,
    lr: float = 0.08,
) -> EmergenceResult:
    agents = [Agent(i, n_objects, n_signals) for i in range(n_agents)]

    success_history = []
    entropy_history = []
    window = []

    for round_num in range(rounds):
        # Pick two agents, one speaks, one listens
        speaker_agent, listener_agent = random.sample(agents, 2)
        obj = random.randint(0, n_objects - 1)

        signal = speaker_agent.speak(obj)
        guess = listener_agent.listen(signal)
        success = int(guess == obj)
        window.append(success)
        if len(window) > 100:
            window.pop(0)

        if success:
            speaker_agent.reinforce_speaker(obj, signal, 1.0, lr)
            listener_agent.reinforce_listener(signal, obj, 1.0, lr)
        else:
            # Penalize slightly — discourages random signals
            speaker_agent.reinforce_speaker(obj, signal, -0.1, lr * 0.5)

        if round_num % 100 == 0:
            success_history.append(sum(window) / len(window) if window else 0)
            avg_entropy = sum(policy_entropy(a) for a in agents) / n_agents
            entropy_history.append(avg_entropy)

    final_rate = sum(window) / len(window) if window else 0
    consensus, topography = measure_consensus(agents, n_objects, n_signals)

    return EmergenceResult(
        n_agents=n_agents,
        n_objects=n_objects,
        n_signals=n_signals,
        rounds=rounds,
        success_rate_history=success_history,
        final_success_rate=final_rate,
        topography=topography,
        consensus=consensus,
        entropy_history=entropy_history,
        emerged=(final_rate > 0.7 and consensus > 0.7),
    )
