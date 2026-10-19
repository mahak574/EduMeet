"""
Synthetic Matching Engine Simulation Benchmark (EduMeet Phase 3)
Evaluates NetworkX Maximum Weight Matching across synthetic students
with realistic complementary strengths, availability windows, and languages.
"""

import math
import random
import time
from typing import Dict, List, Tuple
import networkx as nx

TOPICS_DSA = [
    "arrays-and-hashing",
    "linked-lists-and-stacks",
    "trees-and-graphs",
    "dynamic-programming",
]

TOPICS_DBMS = [
    "relational-schema-and-sql",
    "indexing-and-query-opt",
    "transactions-and-acid",
    "concurrency-and-recovery",
]

ALL_TOPICS = TOPICS_DSA + TOPICS_DBMS


def calculate_topic_gain(teacher_score: float, learner_score: float) -> float:
    knowledge_gap = max(0.0, 80.0 - learner_score)
    competency_advantage = max(0.0, teacher_score - 60.0)
    return round((knowledge_gap * competency_advantage) / (80.0 * 40.0), 4)


def generate_synthetic_student(idx: int) -> dict:
    # 2 random strength topics (score 70-95), 2 growth topics (score 20-45), rest average (45-65)
    shuffled_topics = list(ALL_TOPICS)
    random.shuffle(shuffled_topics)
    strengths = shuffled_topics[:2]
    growth = shuffled_topics[2:4]

    scores: Dict[str, float] = {}
    for t in ALL_TOPICS:
        if t in strengths:
            scores[t] = round(random.uniform(70.0, 95.0), 1)
        elif t in growth:
            scores[t] = round(random.uniform(20.0, 45.0), 1)
        else:
            scores[t] = round(random.uniform(48.0, 62.0), 1)

    # 3-5 random active weekday slots (e.g. 18:00 - 21:00)
    available_days = random.sample(range(7), k=random.randint(3, 5))

    return {
        "id": f"student_{idx:03d}",
        "scores": scores,
        "available_days": set(available_days),
        "style": random.choice(["example_heavy", "socratic", "visual", "theoretical"]),
        "languages": ["en"] if random.random() < 0.85 else ["en", "es"],
        "no_shows": 0 if random.random() < 0.9 else random.randint(1, 2),
    }


def run_benchmark(num_students: int = 100):
    print(f"\n========================================================")
    print(f"EduMeet Matching Engine Benchmark: {num_students} Synthetic Students")
    print(f"========================================================")

    random.seed(42)
    students = [generate_synthetic_student(i) for i in range(num_students)]

    start_time = time.perf_counter()

    # Build Graph
    G = nx.Graph()
    for s in students:
        G.add_node(s["id"])

    edge_count = 0
    weights = []

    for i in range(num_students):
        s_a = students[i]
        for j in range(i + 1, num_students):
            s_b = students[j]

            # Common language check
            if not (set(s_a["languages"]) & set(s_b["languages"])):
                continue

            # Availability overlap check
            common_days = s_a["available_days"] & s_b["available_days"]
            if not common_days:
                continue

            # Find best reciprocal topic pair
            best_gain = 0.0
            for t_a in ALL_TOPICS:
                g_ab = calculate_topic_gain(s_a["scores"][t_a], s_b["scores"][t_a])
                if g_ab <= 0:
                    continue
                for t_b in ALL_TOPICS:
                    if t_a == t_b:
                        continue
                    g_ba = calculate_topic_gain(s_b["scores"][t_b], s_a["scores"][t_b])
                    if g_ba <= 0:
                        continue
                    reciprocal = min(g_ab, g_ba)
                    if reciprocal > best_gain:
                        best_gain = reciprocal

            if best_gain > 0.0:
                m_style = 1.1 if s_a["style"] == s_b["style"] else 1.0
                m_avail = min(1.0, len(common_days) / 3.0)
                m_lang = 1.15
                penalty = math.exp(-0.5 * (s_a["no_shows"] + s_b["no_shows"]))

                w = best_gain * m_style * m_avail * m_lang * penalty
                G.add_edge(s_a["id"], s_b["id"], weight=w)
                edge_count += 1
                weights.append(w)

    graph_time = time.perf_counter() - start_time

    # Run Max Weight Matching
    match_start = time.perf_counter()
    matches = nx.max_weight_matching(G, maxcardinality=True, weight="weight")
    match_time = time.perf_counter() - match_start

    matched_students = len(matches) * 2
    efficiency = (matched_students / num_students) * 100.0

    print(f"Total Nodes (Students)   : {num_students}")
    print(f"Candidate Edges Formed   : {edge_count}")
    print(f"Graph Construction Time  : {graph_time * 1000:.2f} ms")
    print(f"Algorithm Execution Time : {match_time * 1000:.2f} ms")
    print(f"Total Pairs Matched      : {len(matches)} ({matched_students} students)")
    print(f"Pairing Efficiency       : {efficiency:.1f}%")
    if matches:
        matched_weights = [G[u][v]["weight"] for u, v in matches]
        print(f"Average Pair Weight      : {sum(matched_weights) / len(matched_weights):.4f}")
        print(f"Max Pair Weight          : {max(matched_weights):.4f}")
    print(f"========================================================\n")


if __name__ == "__main__":
    run_benchmark(50)
    run_benchmark(100)
    run_benchmark(200)
