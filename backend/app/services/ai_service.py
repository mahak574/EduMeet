import json
import logging
from typing import Any, Dict, List, Optional
from beanie import PydanticObjectId
from fastapi import HTTPException, status
import httpx

from app.config import settings
from app.models.consolidated import Session, User
from app.schemas.ai import (
    CoachExplainRequest,
    CoachExplainResponse,
    LessonPhaseGuide,
    SessionPlanResponse,
    TopicPlan,
)
from app.services.llm_provider import (
    LLMExplanationOutput,
    LLMPlanOutput,
    LLMProvider,
    get_default_llm_provider,
)

logger = logging.getLogger(__name__)

# Curated, deterministic pedagogical blueprints for all Phase 2 syllabus topics
CURATED_PEDAGOGICAL_GUIDES: Dict[str, Dict[str, Any]] = {
    "arrays-and-hashing": {
        "title": "Arrays & Hash Maps: Optimal Lookups & Two Pointers",
        "starter_code": "# Two Sum Pattern\ndef find_pair(nums: list[int], target: int) -> list[int]:\n    seen = {}\n    for i, num in enumerate(nums):\n        diff = target - num\n        if diff in seen:\n            return [seen[diff], i]\n        seen[num] = i\n    return []\n",
        "phases": [
            LessonPhaseGuide(
                phase_name="Concept Foundation (0-7 min)",
                duration_minutes=7,
                objectives=["Understand contiguous memory layout", "Explain O(1) hash bucket amortized lookup vs O(n) brute-force"],
                discussion_prompts=["Why does array indexing take O(1) time?", "What happens during a hash collision?"],
                checklist=["Illustrated contiguous memory indexing", "Drew a hash map bucket diagram"],
            ),
            LessonPhaseGuide(
                phase_name="Algorithmic Deep Dive & Live Code (7-20 min)",
                duration_minutes=13,
                objectives=["Walk through Two Sum / Two Pointers pattern", "Trace space-time trade-off: O(n) space for O(n) time"],
                discussion_prompts=["Can we solve this in O(1) auxiliary space if the array is sorted?", "How do two pointers converge?"],
                checklist=["Shared code in collaborative editor", "Walked through an edge case with duplicates"],
            ),
            LessonPhaseGuide(
                phase_name="Peer Question Formulation (20-25 min)",
                duration_minutes=5,
                objectives=["Formulate 2-3 conceptual check questions for your partner", "Prepare an edge-case test"],
                discussion_prompts=["What is an input that breaks simple array assumptions?"],
                checklist=["Entered peer quiz questions", "Confirmed partner understanding"],
            ),
        ],
    },
    "linked-lists-and-stacks": {
        "title": "Linked Lists & Stacks: Pointer Manipulation & LIFO Order",
        "starter_code": "class ListNode:\n    def __init__(self, val=0, next=None):\n        self.val = val\n        self.next = next\n\ndef reverse_list(head: ListNode) -> ListNode:\n    prev, curr = None, head\n    while curr:\n        nxt = curr.next\n        curr.next = prev\n        prev = curr\n        curr = nxt\n    return prev\n",
        "phases": [
            LessonPhaseGuide(
                phase_name="Pointer Mechanics (0-7 min)",
                duration_minutes=7,
                objectives=["Contrast dynamic node allocation with contiguous arrays", "Differentiate singly vs doubly linked lists"],
                discussion_prompts=["Why can't we access list[i] in O(1) time?", "Why are sentinel dummy nodes useful?"],
                checklist=["Sketched nodes and next pointers on whiteboard", "Highlighted null pointer pitfalls"],
            ),
            LessonPhaseGuide(
                phase_name="Pointer Reversal & Monotonic Stacks (7-20 min)",
                duration_minutes=13,
                objectives=["Demonstrate three-pointer reversal (prev, curr, next)", "Explain Next Greater Element using monotonic stack"],
                discussion_prompts=["What happens if we overwrite curr.next before saving next?", "How does LIFO property enforce order?"],
                checklist=["Live-traced list reversal step by step", "Verified terminating condition"],
            ),
            LessonPhaseGuide(
                phase_name="Peer Verification (20-25 min)",
                duration_minutes=5,
                objectives=["Draft peer quiz testing cycle detection or stack boundaries", "Review partner questions"],
                discussion_prompts=["How would Floyd's Tortoise and Hare detect a cycle?"],
                checklist=["Authored peer quiz question on pointer state", "Ready for quiz exchange"],
            ),
        ],
    },
    "trees-and-graphs": {
        "title": "Trees & Graphs: Traversal (BFS/DFS) & Invariants",
        "starter_code": "from collections import deque\n\ndef bfs_level_order(root):\n    if not root: return []\n    queue = deque([root])\n    res = []\n    while queue:\n        level = []\n        for _ in range(len(queue)):\n            node = queue.popleft()\n            level.append(node.val)\n            if node.left: queue.append(node.left)\n            if node.right: queue.append(node.right)\n        res.append(level)\n    return res\n",
        "phases": [
            LessonPhaseGuide(
                phase_name="Tree Invariants & Representations (0-7 min)",
                duration_minutes=7,
                objectives=["Understand BST invariant (left < node < right)", "Adjacency list vs adjacency matrix for graphs"],
                discussion_prompts=["What makes a tree a specialized graph?", "When is BFS preferable to DFS?"],
                checklist=["Drew binary tree on whiteboard", "Identified root, leaf, and subtree"],
            ),
            LessonPhaseGuide(
                phase_name="Traversals & Recursion Tree (7-20 min)",
                duration_minutes=13,
                objectives=["Trace recursion stack for DFS (Pre/In/Post-order)", "Demonstrate queue-based level order BFS"],
                discussion_prompts=["Why does In-Order traversal of a BST yield sorted order?", "How do visited sets prevent infinite graph cycles?"],
                checklist=["Traced recursion depth and base cases", "Demonstrated cycle handling"],
            ),
            LessonPhaseGuide(
                phase_name="Peer Question Crafting (20-25 min)",
                duration_minutes=5,
                objectives=["Write questions testing tree traversal sequence or height"],
                discussion_prompts=["Can your partner tell BFS from DFS output?"],
                checklist=["Drafted question for peer exchange"],
            ),
        ],
    },
    "dynamic-programming": {
        "title": "Dynamic Programming: Overlapping Subproblems & Memoization",
        "starter_code": "def climb_stairs(n: int) -> int:\n    if n <= 2: return n\n    dp = [0] * (n + 1)\n    dp[1], dp[2] = 1, 2\n    for i in range(3, n + 1):\n        dp[i] = dp[i - 1] + dp[i - 2]\n    return dp[n]\n",
        "phases": [
            LessonPhaseGuide(
                phase_name="From Recursion to Subproblems (0-7 min)",
                duration_minutes=7,
                objectives=["Identify optimal substructure", "Recognize redundant calculations in recursion trees"],
                discussion_prompts=["Why does naive Fibonacci run in O(2^n)?", "What is the state transition relation?"],
                checklist=["Drew recursion tree with duplicate calls highlighted"],
            ),
            LessonPhaseGuide(
                phase_name="Memoization vs Tabulation (7-20 min)",
                duration_minutes=13,
                objectives=["Top-down memoization with hash table/cache", "Bottom-up tabulation with space optimization"],
                discussion_prompts=["How can we reduce O(n) space to O(1) in Fibonacci?", "What is base case initialization?"],
                checklist=["Wrote recurrence relation dp[i] = f(dp[i-1], ...)", "Walked through iterative table fill"],
            ),
            LessonPhaseGuide(
                phase_name="Peer Verification (20-25 min)",
                duration_minutes=5,
                objectives=["Author a peer question on transition relation or DP state dimension"],
                discussion_prompts=["What does dp[i][j] represent in a 2D problem?"],
                checklist=["Submitted peer test questions"],
            ),
        ],
    },
    "relational-schema-and-sql": {
        "title": "Relational Schema & SQL: Joins, Aggregations & Normalization",
        "starter_code": "-- Inner Join with Group By\nSELECT d.dept_name, COUNT(e.id) AS total_employees, AVG(e.salary) AS avg_sal\nFROM departments d\nINNER JOIN employees e ON d.id = e.dept_id\nWHERE e.status = 'active'\nGROUP BY d.dept_name\nHAVING COUNT(e.id) >= 5;\n",
        "phases": [
            LessonPhaseGuide(
                phase_name="Relational Foundations (0-7 min)",
                duration_minutes=7,
                objectives=["Entity-relationship modeling", "Primary key vs Foreign key referential integrity", "1NF to 3NF normalization"],
                discussion_prompts=["What anomalies occur in un-normalized tables (insert/update/delete)?", "What is a composite primary key?"],
                checklist=["Drawn ER relationships", "Explained foreign key constraints"],
            ),
            LessonPhaseGuide(
                phase_name="SQL Query Execution Pipeline (7-20 min)",
                duration_minutes=13,
                objectives=["Explain logical query processing order: FROM -> WHERE -> GROUP BY -> HAVING -> SELECT -> ORDER BY", "INNER vs LEFT OUTER joins"],
                discussion_prompts=["Why can't we use column aliases in the WHERE clause?", "What happens to unmatched rows in LEFT JOIN?"],
                checklist=["Executed sample query in editor", "Highlighted WHERE vs HAVING differences"],
            ),
            LessonPhaseGuide(
                phase_name="Peer Quiz Authoring (20-25 min)",
                duration_minutes=5,
                objectives=["Craft questions testing join output rows or GROUP BY syntax"],
                discussion_prompts=["Ask partner to predict output count on NULL match"],
                checklist=["Drafted peer SQL questions"],
            ),
        ],
    },
    "indexing-and-query-opt": {
        "title": "Indexing & Query Optimization: B+ Trees & Execution Plans",
        "starter_code": "-- Inspecting Query Execution Plan\nEXPLAIN ANALYZE\nSELECT * FROM orders\nWHERE customer_id = 42\n  AND created_at >= '2026-01-01'\nORDER BY created_at DESC;\n",
        "phases": [
            LessonPhaseGuide(
                phase_name="B+ Tree Architecture (0-7 min)",
                duration_minutes=7,
                objectives=["Explain fanout and shallow depth in disk storage", "Why B+ tree leaves form a linked list for range queries"],
                discussion_prompts=["Why don't relational databases use binary search trees for disk indexes?", "What is a clustered vs non-clustered index?"],
                checklist=["Sketched B+ tree internal nodes and linked leaf pages"],
            ),
            LessonPhaseGuide(
                phase_name="Composite Indexes & EXPLAIN Plans (7-20 min)",
                duration_minutes=13,
                objectives=["The Leftmost Prefix rule in multi-column indexes", "Index Scan vs Index Only Scan vs Sequential Table Scan"],
                discussion_prompts=["Why does WHERE col_b = 5 fail to use an index on (col_a, col_b)?", "How do selective predicates improve performance?"],
                checklist=["Walked through query plan cost estimates", "Identified indexing anti-patterns"],
            ),
            LessonPhaseGuide(
                phase_name="Peer Evaluation (20-25 min)",
                duration_minutes=5,
                objectives=["Formulate peer quiz item on index eligibility or covering index"],
                discussion_prompts=["Can an index cover a query without touching table pages?"],
                checklist=["Peer quiz written and saved"],
            ),
        ],
    },
    "transactions-and-acid": {
        "title": "Transactions & ACID Guarantees: Isolation & Durability",
        "starter_code": "BEGIN TRANSACTION;\n  UPDATE accounts SET balance = balance - 100 WHERE id = 1;\n  UPDATE accounts SET balance = balance + 100 WHERE id = 2;\nCOMMIT;\n",
        "phases": [
            LessonPhaseGuide(
                phase_name="ACID Properties Breakdown (0-7 min)",
                duration_minutes=7,
                objectives=["Define Atomicity (all-or-nothing), Consistency, Isolation, and Durability (WAL write-ahead log)"],
                discussion_prompts=["How does the database roll back if power fails midway?", "What is Write-Ahead Logging?"],
                checklist=["Explained bank transfer transaction example", "Defined commit vs rollback"],
            ),
            LessonPhaseGuide(
                phase_name="Isolation Levels & Read Phenomena (7-20 min)",
                duration_minutes=13,
                objectives=["The four SQL standard levels: Read Uncommitted, Read Committed, Repeatable Read, Serializable", "Dirty reads, non-repeatable reads, and phantom reads"],
                discussion_prompts=["What is a dirty read?", "How does MVCC (Multi-Version Concurrency Control) eliminate read locks?"],
                checklist=["Drew timeline of concurrent transactions", "Demonstrated lost update anomaly"],
            ),
            LessonPhaseGuide(
                phase_name="Peer Testing (20-25 min)",
                duration_minutes=5,
                objectives=["Author a peer quiz question comparing isolation level anomalies"],
                discussion_prompts=["Ask partner which phenomenon Repeatable Read prevents"],
                checklist=["Peer quiz submitted for exchange"],
            ),
        ],
    },
    "concurrency-and-recovery": {
        "title": "Concurrency Control & Crash Recovery: Two-Phase Locking & ARIES",
        "starter_code": "-- Two-Phase Locking (2PL) Invariant:\n-- Growing phase: Acquire locks (S/X), release none.\n-- Shrinking phase: Release locks, acquire none.\n-- Deadlock Detection: Wait-For Graph cycle detection\n",
        "phases": [
            LessonPhaseGuide(
                phase_name="Two-Phase Locking (2PL) Mechanics (0-7 min)",
                duration_minutes=7,
                objectives=["Shared (S) vs Exclusive (X) lock compatibility", "Strict 2PL and serializability guarantee"],
                discussion_prompts=["What prevents cascading aborts in Strict 2PL?", "Why must all exclusive locks be held until commit?"],
                checklist=["Drew lock compatibility matrix", "Illustrated growing and shrinking phases"],
            ),
            LessonPhaseGuide(
                phase_name="Deadlocks & ARIES Recovery (7-20 min)",
                duration_minutes=13,
                objectives=["Deadlock detection via Wait-For Graph cycle check", "ARIES recovery phases: Analysis, Redo (history repeating), Undo (rolling back losers)"],
                discussion_prompts=["How does a database break deadlocks?", "Why do we Redo before Undo during recovery?"],
                checklist=["Traced Wait-For Graph cycle", "Outlined ARIES recovery sequence"],
            ),
            LessonPhaseGuide(
                phase_name="Peer Verification (20-25 min)",
                duration_minutes=5,
                objectives=["Write questions on 2PL rules or ARIES recovery log entries"],
                discussion_prompts=["Can partner identify a deadlock from resource requests?"],
                checklist=["Ready for mutual testing exchange"],
            ),
        ],
    },
}


class AIService:
    _llm_provider: Optional[LLMProvider] = None

    @classmethod
    def set_llm_provider(cls, provider: Optional[LLMProvider]):
        cls._llm_provider = provider

    @classmethod
    def _build_default_plan(
        cls,
        subject: str,
        topic: str,
        teacher: User,
        learner: User,
    ) -> TopicPlan:
        guide = CURATED_PEDAGOGICAL_GUIDES.get(topic)
        if not guide:
            title = f"{topic.replace('-', ' ').title()} ({subject.upper()})"
            starter = f"# Topic Starter for {title}\n"
            phases = [
                LessonPhaseGuide(
                    phase_name="Conceptual Foundations (0-7 min)",
                    duration_minutes=7,
                    objectives=[f"Introduce foundational principles of {title}", "Clarify prerequisites and mental model"],
                    discussion_prompts=["What are the core operations and edge cases?", "Why is this concept crucial?"],
                    checklist=["Visualized concept on whiteboard", "Confirmed partner comprehension"],
                ),
                LessonPhaseGuide(
                    phase_name="Hands-on Code & Problem Solving (7-20 min)",
                    duration_minutes=13,
                    objectives=["Walk through representative algorithm/query", "Analyze time and space complexity"],
                    discussion_prompts=["Can we optimize the bottleneck?", "What breaks if input is empty or null?"],
                    checklist=["Co-authored solution in editor", "Traced execution flow"],
                ),
                LessonPhaseGuide(
                    phase_name="Peer Question Formulation (20-25 min)",
                    duration_minutes=5,
                    objectives=["Author 2-3 targeted peer quiz questions", "Prepare partner for the reciprocal test"],
                    discussion_prompts=["What was the trickiest part of today's concept?"],
                    checklist=["Saved peer questions in quiz tab"],
                ),
            ]
        else:
            title = guide["title"]
            starter = guide["starter_code"]
            phases = guide["phases"]

        return TopicPlan(
            topic_name=title,
            subject_slug=subject,
            subtopic_slug=topic,
            teacher_name=teacher.full_name,
            learner_name=learner.full_name,
            phases=phases,
            starter_code_or_query=starter,
        )

    @classmethod
    async def generate_session_plan(
        cls,
        session_id: PydanticObjectId,
        current_user: User,
    ) -> SessionPlanResponse:
        session = await Session.get(session_id)
        if not session:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found.")

        user_ids = [p.user_id for p in session.participants]
        if current_user.id not in user_ids:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Participant access only.")

        user_a_p = next((p for p in session.participants if p.role == "teacher_a"), session.participants[0])
        user_b_p = next((p for p in session.participants if p.role == "teacher_b"), session.participants[1])

        user_a = await User.get(user_a_p.user_id)
        user_b = await User.get(user_b_p.user_id)

        if not user_a or not user_b:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session participants missing.")

        # Mutual AI Consent Check
        ai_consent_mutual = bool(user_a.ai_consent and user_b.ai_consent)

        # Baseline deterministic pedagogical plan
        plan_a = cls._build_default_plan(
            subject=user_a_p.teach_subject_slug,
            topic=user_a_p.teach_topic_slug,
            teacher=user_a,
            learner=user_b,
        )
        plan_b = cls._build_default_plan(
            subject=user_b_p.teach_subject_slug,
            topic=user_b_p.teach_topic_slug,
            teacher=user_b,
            learner=user_a,
        )

        guidelines = [
            "Structure: 20 minutes interactive teaching + 5 minutes authoring 2 peer questions.",
            "Reciprocal Exchange: Roles swap smoothly at the 25-minute mark.",
            "Followup: 10 minutes allocated for mutual quiz testing and mistake discussion.",
            "Both peers share equal voice time to maximize retention via the Protégé Effect.",
        ]

        # If either opted out, return deterministic fallback
        if not ai_consent_mutual:
            notice = (
                "Operating with deterministic pedagogical blueprint. "
                "Mutual AI consent is required for generative AI customization."
            )
            return SessionPlanResponse(
                session_id=session.id,
                is_llm_generated=False,
                ai_consent_mutual=False,
                plan_teacher_a=plan_a,
                plan_teacher_b=plan_b,
                general_guidelines=guidelines,
                notice=notice,
            )

        # Attempt LLM enhancement via LLMProvider
        llm = cls._llm_provider or get_default_llm_provider()
        try:
            # Anonymized prompt: never send real names to the LLM (fixed session.topic_a bug)
            prompt = (
                f"Create an optimal 20-minute peer lesson guide for reciprocal study pair.\n"
                f"Teacher 1: Student A teaching {user_a_p.teach_topic_slug} ({user_a_p.teach_subject_slug}) to Student B.\n"
                f"Teacher 2: Student B teaching {user_b_p.teach_topic_slug} ({user_b_p.teach_subject_slug}) to Student A.\n"
                f"Return JSON format with keys: objectives (array of strings), discussion_prompts (array of strings), checklist (array of strings)."
            )
            completion = await llm.generate_completion(
                system_prompt="You are an expert pedagogical engineering coach.",
                user_prompt=prompt,
            )
            if completion:
                raw_json = json.loads(completion)
                # Validate output with Pydantic
                validated_output = LLMPlanOutput.model_validate(raw_json)
                if validated_output.objectives or validated_output.discussion_prompts:
                    # Apply validated LLM output to customize plan
                    if len(plan_a.phases) > 0 and validated_output.objectives:
                        plan_a.phases[0].objectives = validated_output.objectives[:2]
                    if len(plan_a.phases) > 1 and validated_output.discussion_prompts:
                        plan_a.phases[1].discussion_prompts = validated_output.discussion_prompts[:2]
                    if len(plan_b.phases) > 0 and validated_output.objectives:
                        plan_b.phases[0].objectives = validated_output.objectives[:2]
                    if len(plan_b.phases) > 1 and validated_output.discussion_prompts:
                        plan_b.phases[1].discussion_prompts = validated_output.discussion_prompts[:2]

                    # ONLY set is_llm_generated=True when LLM output is actually used
                    return SessionPlanResponse(
                        session_id=session.id,
                        is_llm_generated=True,
                        ai_consent_mutual=True,
                        plan_teacher_a=plan_a,
                        plan_teacher_b=plan_b,
                        general_guidelines=guidelines,
                        notice="Session plan dynamically enhanced by EduMeet Pedagogical AI Coach.",
                    )
        except Exception as exc:
            logger.warning("LLM generation encountered error, falling back gracefully: %s", exc)

        return SessionPlanResponse(
            session_id=session.id,
            is_llm_generated=False,
            ai_consent_mutual=ai_consent_mutual,
            plan_teacher_a=plan_a,
            plan_teacher_b=plan_b,
            general_guidelines=guidelines,
            notice="Operating with deterministic pedagogical blueprint (LLM fallback applied).",
        )

    @classmethod
    async def explain_concept(
        cls,
        request: CoachExplainRequest,
        user: User,
    ) -> CoachExplainResponse:
        # Check user consent
        if not user.ai_consent:
            # Deterministic pedagogical breakdown
            topic_key = request.topic_slug
            guide = CURATED_PEDAGOGICAL_GUIDES.get(topic_key)
            title = guide["title"] if guide else request.concept_or_question

            analogy = (
                f"Think of {request.concept_or_question} like an organized library catalogue: "
                "instead of inspecting every book shelf (brute force), an index guides you directly to the target aisle."
            )
            explanation = (
                f"In computer science, {request.concept_or_question} balances space and time complexity. "
                "By establishing strong invariants (e.g. sorted order, pointer links, or memoized tables), "
                "we eliminate redundant computation and reduce worst-case operational costs."
            )
            takeaways = [
                "Always identify the core invariant before writing code.",
                "Verify base cases (empty inputs, single elements, null pointers).",
                "Measure space-time trade-offs to justify optimal design.",
            ]
            practice = f"How would your algorithm behave if the input for {request.concept_or_question} contained all duplicate values?"

            return CoachExplainResponse(
                concept=request.concept_or_question,
                is_llm_generated=False,
                analogy=analogy,
                explanation=explanation,
                key_takeaways=takeaways,
                practice_question=practice,
            )

        # Generative AI Coach via LLMProvider
        llm = cls._llm_provider or get_default_llm_provider()
        try:
            # Anonymized prompt: never send real user names to the LLM
            prompt = (
                f"Explain the concept '{request.concept_or_question}' in {request.subject_slug} ({request.topic_slug}).\n"
                f"Student confusion note: '{request.student_confusion or 'None provided'}'.\n"
                f"Provide a clear analogy, step-by-step breakdown, 3 key takeaways, and 1 quick check question. "
                f"Return JSON format with keys: title, analogy, explanation, key_takeaway."
            )
            completion = await llm.generate_completion(
                system_prompt="You are a friendly Socratic computer science mentor.",
                user_prompt=prompt,
            )
            if completion:
                raw_json = json.loads(completion)
                # Validate output with Pydantic
                validated = LLMExplanationOutput.model_validate(raw_json)
                if validated.analogy and validated.explanation:
                    return CoachExplainResponse(
                        concept=request.concept_or_question,
                        is_llm_generated=True,
                        analogy=validated.analogy,
                        explanation=validated.explanation,
                        key_takeaways=[validated.key_takeaway],
                        practice_question=f"How would you apply {request.concept_or_question} in a real-world system?",
                    )
        except Exception as exc:
            logger.warning("Generative coach call failed, falling back: %s", exc)

        return await cls.explain_concept(
            CoachExplainRequest(
                concept_or_question=request.concept_or_question,
                subject_slug=request.subject_slug,
                topic_slug=request.topic_slug,
                student_confusion=request.student_confusion,
            ),
            User(**{**user.model_dump(), "ai_consent": False}),  # trigger fallback
        )
