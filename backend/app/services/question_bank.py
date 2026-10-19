import logging
from datetime import datetime, timezone
from typing import List, Dict, Any
from app.models.consolidated import Question, QuestionOption

logger = logging.getLogger(__name__)

# Canonical seed question bank for Phase 2:
# Subjects: DSA and DBMS
# 4 Topics per subject (8 topics total)
SEED_QUESTIONS: List[Dict[str, Any]] = [
    # =========================================================================
    # 1. DSA: arrays-and-hashing
    # =========================================================================
    {
        "subject_slug": "dsa",
        "topic_slug": "arrays-and-hashing",
        "subtopic_slug": "hash-tables",
        "difficulty": "easy",
        "prompt_text": "What is the average-case time complexity of inserting a key-value pair into a hash map?",
        "options": [
            {"id": "A", "text": "O(1)"},
            {"id": "B", "text": "O(log n)"},
            {"id": "C", "text": "O(n)"},
            {"id": "D", "text": "O(n log n)"},
        ],
        "correct_option_id": "A",
        "explanation": "Assuming a uniform hash distribution and appropriate load factor, average-case insertion in a hash table takes O(1) constant time.",
    },
    {
        "subject_slug": "dsa",
        "topic_slug": "arrays-and-hashing",
        "subtopic_slug": "two-pointers",
        "difficulty": "medium",
        "prompt_text": "In a sorted array, which technique finds two numbers that sum to a target with O(n) time and O(1) auxiliary space?",
        "code_snippet": "def two_sum_sorted(arr: list[int], target: int) -> tuple[int, int]:\n    # Optimal approach\n    pass",
        "options": [
            {"id": "A", "text": "Binary search on every element (O(n log n))"},
            {"id": "B", "text": "Two pointers from opposite ends (left=0, right=len-1)"},
            {"id": "C", "text": "Hash set lookups (O(n) auxiliary space)"},
            {"id": "D", "text": "Nested loops (O(n^2))"},
        ],
        "correct_option_id": "B",
        "explanation": "Because the array is already sorted, opposite-end two-pointers adjust boundaries based on sum comparison in O(n) time and O(1) auxiliary space.",
    },
    {
        "subject_slug": "dsa",
        "topic_slug": "arrays-and-hashing",
        "subtopic_slug": "prefix-sums",
        "difficulty": "hard",
        "prompt_text": "To find the number of contiguous subarrays that sum to k in an array with negative numbers, what data structure should store prefix sums?",
        "options": [
            {"id": "A", "text": "A standard sliding window with two pointers"},
            {"id": "B", "text": "A hash map storing prefix sum frequencies: {prefix_sum: count}"},
            {"id": "C", "text": "A monotonic max-heap"},
            {"id": "D", "text": "A segment tree with point updates"},
        ],
        "correct_option_id": "B",
        "explanation": "When arrays contain negative numbers, the prefix sum is non-monotonic, invalidating a two-pointer sliding window. Storing prefix sum frequencies in a hash map allows O(1) lookup for (current_prefix - k), solving in O(n) time.",
    },
    {
        "subject_slug": "dsa",
        "topic_slug": "arrays-and-hashing",
        "subtopic_slug": "hash-sets",
        "difficulty": "easy",
        "prompt_text": "Which operation can determine if an array contains duplicate integers in O(n) time?",
        "options": [
            {"id": "A", "text": "Iterating while adding elements to a Hash Set and checking for membership"},
            {"id": "B", "text": "Checking every pair with nested for-loops"},
            {"id": "C", "text": "Computing the factorial of array length"},
            {"id": "D", "text": "In-place quicksort and scanning for duplicates"},
        ],
        "correct_option_id": "A",
        "explanation": "A hash set allows O(1) average lookup and insertion, enabling duplicate detection in single-pass O(n) time.",
    },

    # =========================================================================
    # 2. DSA: linked-lists-and-stacks
    # =========================================================================
    {
        "subject_slug": "dsa",
        "topic_slug": "linked-lists-and-stacks",
        "subtopic_slug": "cycle-detection",
        "difficulty": "easy",
        "prompt_text": "What is Floyd's Cycle-Finding Algorithm (Tortoise and Hare) space complexity?",
        "options": [
            {"id": "A", "text": "O(1)"},
            {"id": "B", "text": "O(n)"},
            {"id": "C", "text": "O(log n)"},
            {"id": "D", "text": "O(n^2)"},
        ],
        "correct_option_id": "A",
        "explanation": "Floyd's algorithm uses two pointer references (slow moving 1 step, fast moving 2 steps) without allocating any supplementary nodes, yielding O(1) space complexity.",
    },
    {
        "subject_slug": "dsa",
        "topic_slug": "linked-lists-and-stacks",
        "subtopic_slug": "monotonic-stack",
        "difficulty": "medium",
        "prompt_text": "What data structure solves the 'Next Greater Element' problem for each item in an array in O(n) total time?",
        "options": [
            {"id": "A", "text": "A monotonic decreasing stack storing indices"},
            {"id": "B", "text": "A balanced binary search tree"},
            {"id": "C", "text": "A FIFO queue"},
            {"id": "D", "text": "A circular doubly-linked list"},
        ],
        "correct_option_id": "A",
        "explanation": "A monotonic stack pushes each index once and pops at most once, providing next greater element resolution in amortized O(1) per element, O(n) overall.",
    },
    {
        "subject_slug": "dsa",
        "topic_slug": "linked-lists-and-stacks",
        "subtopic_slug": "stack-evaluation",
        "difficulty": "hard",
        "prompt_text": "In Dijkstra's Two-Stack Algorithm for parsing infix expressions, what triggers evaluating an operator on the stack?",
        "options": [
            {"id": "A", "text": "Encountering an open parenthesis '('"},
            {"id": "B", "text": "Encountering a new operand"},
            {"id": "C", "text": "Encountering an operator with lower or equal precedence than the top of operator stack"},
            {"id": "D", "text": "Reaching the midpoint of the input string"},
        ],
        "correct_option_id": "C",
        "explanation": "When an incoming operator has less or equal precedence compared to the operator on top of the stack, higher-precedence operations must be popped and computed first.",
    },
    {
        "subject_slug": "dsa",
        "topic_slug": "linked-lists-and-stacks",
        "subtopic_slug": "singly-linked-list",
        "difficulty": "easy",
        "prompt_text": "To reverse a singly linked list iteratively in O(n) time and O(1) space, how many pointer variables are required?",
        "options": [
            {"id": "A", "text": "Three pointers: prev, curr, and next_node"},
            {"id": "B", "text": "One pointer"},
            {"id": "C", "text": "A full secondary array of pointers"},
            {"id": "D", "text": "None, recursion is required"},
        ],
        "correct_option_id": "A",
        "explanation": "Reversing link directions iteratively requires tracking the previous node (prev), the current node (curr), and preserving the rest of the list (next_node) before updating curr.next.",
    },

    # =========================================================================
    # 3. DSA: trees-and-graphs
    # =========================================================================
    {
        "subject_slug": "dsa",
        "topic_slug": "trees-and-graphs",
        "subtopic_slug": "tree-traversal",
        "difficulty": "easy",
        "prompt_text": "Which tree traversal of a Binary Search Tree (BST) produces keys in ascending sorted order?",
        "options": [
            {"id": "A", "text": "In-order traversal (Left, Root, Right)"},
            {"id": "B", "text": "Pre-order traversal (Root, Left, Right)"},
            {"id": "C", "text": "Post-order traversal (Left, Right, Root)"},
            {"id": "D", "text": "Breadth-first level-order traversal"},
        ],
        "correct_option_id": "A",
        "explanation": "In a BST, all left subtree values are strictly smaller than the root, and right values are greater. Visiting Left -> Root -> Right yields the values in monotonically non-decreasing order.",
    },
    {
        "subject_slug": "dsa",
        "topic_slug": "trees-and-graphs",
        "subtopic_slug": "bfs-shortest-path",
        "difficulty": "medium",
        "prompt_text": "Why is Breadth-First Search (BFS) preferred over Depth-First Search (DFS) for finding the shortest path in an unweighted graph?",
        "options": [
            {"id": "A", "text": "BFS explores vertices in order of increasing distance from the source"},
            {"id": "B", "text": "BFS uses less memory than DFS on wide trees"},
            {"id": "C", "text": "BFS does not require a visited set"},
            {"id": "D", "text": "BFS can handle negative edge weights"},
        ],
        "correct_option_id": "A",
        "explanation": "Because BFS explores frontier vertices level-by-level using a FIFO queue, the first time the destination vertex is visited is guaranteed to be via the fewest edges in an unweighted graph.",
    },
    {
        "subject_slug": "dsa",
        "topic_slug": "trees-and-graphs",
        "subtopic_slug": "topological-sort",
        "difficulty": "hard",
        "prompt_text": "What condition causes Kahn's algorithm for topological sorting to fail to include all vertices in the result?",
        "options": [
            {"id": "A", "text": "The graph contains a directed cycle"},
            {"id": "B", "text": "The graph has more than one connected component"},
            {"id": "C", "text": "The graph contains vertices with in-degree 0"},
            {"id": "D", "text": "The graph has self-loops with negative weights"},
        ],
        "correct_option_id": "A",
        "explanation": "Kahn's algorithm repeatedly removes vertices with in-degree 0. If a directed cycle exists, none of the cycle's vertices can ever reach in-degree 0, so the topological output length is less than |V|.",
    },
    {
        "subject_slug": "dsa",
        "topic_slug": "trees-and-graphs",
        "subtopic_slug": "lowest-common-ancestor",
        "difficulty": "medium",
        "prompt_text": "In a BST with unique values, how do you determine if the current node is the Lowest Common Ancestor (LCA) of nodes p and q?",
        "options": [
            {"id": "A", "text": "If (p.val <= curr.val <= q.val) or (q.val <= curr.val <= p.val)"},
            {"id": "B", "text": "Only if curr == p and curr == q"},
            {"id": "C", "text": "If curr has no children"},
            {"id": "D", "text": "If depth(curr) is maximum"},
        ],
        "correct_option_id": "A",
        "explanation": "In a BST, the LCA is the first node along the downward search path where p and q split into opposite subtrees (or one equals curr).",
    },

    # =========================================================================
    # 4. DSA: dynamic-programming
    # =========================================================================
    {
        "subject_slug": "dsa",
        "topic_slug": "dynamic-programming",
        "subtopic_slug": "memoization",
        "difficulty": "easy",
        "prompt_text": "What two key properties must a problem have to be solvable using Dynamic Programming?",
        "options": [
            {"id": "A", "text": "Optimal substructure and overlapping subproblems"},
            {"id": "B", "text": "Greedy choice property and sorted inputs"},
            {"id": "C", "text": "Linear equations and matrix invertibility"},
            {"id": "D", "text": "Divide and conquer with independent disjoint subproblems"},
        ],
        "correct_option_id": "A",
        "explanation": "Dynamic programming applies when the global optimum can be constructed from subproblem optima (optimal substructure) and those subproblems recur repeatedly (overlapping subproblems).",
    },
    {
        "subject_slug": "dsa",
        "topic_slug": "dynamic-programming",
        "subtopic_slug": "0-1-knapsack",
        "difficulty": "medium",
        "prompt_text": "When optimizing space for the 0/1 Knapsack problem from a 2D table dp[i][w] to a 1D array dp[w], how must the capacity loop iterate?",
        "options": [
            {"id": "A", "text": "Backwards from capacity W down to weight of item i"},
            {"id": "B", "text": "Forwards from 0 up to capacity W"},
            {"id": "C", "text": "In random order"},
            {"id": "D", "text": "Alternating between even and odd indices"},
        ],
        "correct_option_id": "A",
        "explanation": "Iterating backwards ensures that dp[w - weight] reflects values from the previous item (i - 1), preventing an item from being counted multiple times as in unbounded knapsack.",
    },
    {
        "subject_slug": "dsa",
        "topic_slug": "dynamic-programming",
        "subtopic_slug": "longest-increasing-subsequence",
        "difficulty": "hard",
        "prompt_text": "What is the optimal time complexity to find the length of the Longest Increasing Subsequence (LIS) in an array of size n?",
        "options": [
            {"id": "A", "text": "O(n log n) using patience sorting with binary search (bisect)"},
            {"id": "B", "text": "O(n) using two pointers"},
            {"id": "C", "text": "O(n^2) standard tabular DP"},
            {"id": "D", "text": "O(2^n) brute force recursion"},
        ],
        "correct_option_id": "A",
        "explanation": "While basic DP is O(n^2), maintaining the tails array of smallest tail values for increasing subsequences of length k allows binary searching in O(log n) per element, achieving O(n log n).",
    },
    {
        "subject_slug": "dsa",
        "topic_slug": "dynamic-programming",
        "subtopic_slug": "coin-change",
        "difficulty": "medium",
        "prompt_text": "In the Coin Change problem (minimum coins to make amount A), what is the base case for dp[0]?",
        "options": [
            {"id": "A", "text": "0 coins needed to make amount 0"},
            {"id": "B", "text": "Infinity (impossible)"},
            {"id": "C", "text": "1 coin"},
            {"id": "D", "text": "-1"},
        ],
        "correct_option_id": "A",
        "explanation": "Zero coins are required to form an amount of zero: dp[0] = 0. All other dp values are initialized to infinity.",
    },

    # =========================================================================
    # 5. DBMS: relational-schema-and-sql
    # =========================================================================
    {
        "subject_slug": "dbms",
        "topic_slug": "relational-schema-and-sql",
        "subtopic_slug": "joins",
        "difficulty": "easy",
        "prompt_text": "Which SQL JOIN returns all rows from the left table and matched rows from the right table, filling unmatched right columns with NULL?",
        "options": [
            {"id": "A", "text": "LEFT OUTER JOIN"},
            {"id": "B", "text": "INNER JOIN"},
            {"id": "C", "text": "CROSS JOIN"},
            {"id": "D", "text": "RIGHT OUTER JOIN"},
        ],
        "correct_option_id": "A",
        "explanation": "LEFT OUTER JOIN preserves every record from the left relation regardless of whether a matching predicate is satisfied in the right table, populating missing attributes with NULL.",
    },
    {
        "subject_slug": "dbms",
        "topic_slug": "relational-schema-and-sql",
        "subtopic_slug": "normalization",
        "difficulty": "medium",
        "prompt_text": "A relation is in Boyce-Codd Normal Form (BCNF) if and only if for every non-trivial functional dependency X -> Y:",
        "options": [
            {"id": "A", "text": "X is a superkey"},
            {"id": "B", "text": "Y is a prime attribute"},
            {"id": "C", "text": "X has no multi-valued dependencies"},
            {"id": "D", "text": "Y is not part of any composite key"},
        ],
        "correct_option_id": "A",
        "explanation": "BCNF eliminates all redundancy caused by functional dependencies by requiring that the determinant X in every non-trivial dependency X -> Y is a superkey of the relation.",
    },
    {
        "subject_slug": "dbms",
        "topic_slug": "relational-schema-and-sql",
        "subtopic_slug": "window-functions",
        "difficulty": "hard",
        "prompt_text": "In SQL window functions, what is the fundamental semantic difference between RANK() and DENSE_RANK()?",
        "options": [
            {"id": "A", "text": "RANK() leaves gaps in ranking numbers after ties; DENSE_RANK() does not"},
            {"id": "B", "text": "DENSE_RANK() can only be computed over partitioned sets"},
            {"id": "C", "text": "RANK() cannot use an ORDER BY clause"},
            {"id": "D", "text": "DENSE_RANK() skips ranks on NULL values"},
        ],
        "correct_option_id": "A",
        "explanation": "If two rows tie for 1st place, RANK() gives both 1 and assigns 3 to the next row (gap). DENSE_RANK() assigns 1 to both ties and 2 to the subsequent row (no gap).",
    },
    {
        "subject_slug": "dbms",
        "topic_slug": "relational-schema-and-sql",
        "subtopic_slug": "group-by-having",
        "difficulty": "easy",
        "prompt_text": "In a SQL query with GROUP BY, which clause filters aggregated group results rather than individual source rows?",
        "options": [
            {"id": "A", "text": "HAVING"},
            {"id": "B", "text": "WHERE"},
            {"id": "C", "text": "ORDER BY"},
            {"id": "D", "text": "LIMIT"},
        ],
        "correct_option_id": "A",
        "explanation": "WHERE filters rows before aggregation; HAVING filters groups after aggregation functions like COUNT, SUM, or AVG have been evaluated.",
    },

    # =========================================================================
    # 6. DBMS: indexing-and-query-opt
    # =========================================================================
    {
        "subject_slug": "dbms",
        "topic_slug": "indexing-and-query-opt",
        "subtopic_slug": "b-plus-trees",
        "difficulty": "easy",
        "prompt_text": "Why do relational database storage engines use B+ Trees rather than standard Binary Search Trees for disk-based indexing?",
        "options": [
            {"id": "A", "text": "High fanout minimizes disk I/O seek operations, and leaf node chaining speeds range scans"},
            {"id": "B", "text": "B+ Trees consume zero RAM in the buffer pool"},
            {"id": "C", "text": "Binary search trees cannot store string keys"},
            {"id": "D", "text": "B+ Trees enforce uniqueness across all columns"},
        ],
        "correct_option_id": "A",
        "explanation": "B+ Tree nodes have a large branching factor (fanout) matching disk page sizes (4KB-16KB), keeping tree height low (typically 3-4 levels) and reducing costly random disk seeks.",
    },
    {
        "subject_slug": "dbms",
        "topic_slug": "indexing-and-query-opt",
        "subtopic_slug": "composite-indexes",
        "difficulty": "medium",
        "prompt_text": "Given a composite index on (department_id, salary), which query predicate CANNOT use the index efficiently?",
        "options": [
            {"id": "A", "text": "WHERE salary > 50000 (without specifying department_id)"},
            {"id": "B", "text": "WHERE department_id = 10 AND salary > 50000"},
            {"id": "C", "text": "WHERE department_id = 10"},
            {"id": "D", "text": "WHERE department_id IN (1, 2) AND salary = 40000"},
        ],
        "correct_option_id": "A",
        "explanation": "Composite B+ Tree indexes adhere to the Leftmost Prefix Rule. Queries filtering only on secondary columns without specifying the leading column cannot perform an index range scan.",
    },
    {
        "subject_slug": "dbms",
        "topic_slug": "indexing-and-query-opt",
        "subtopic_slug": "query-execution-plans",
        "difficulty": "hard",
        "prompt_text": "What is an Index-Only Scan (Covering Index) in modern relational query optimizers?",
        "options": [
            {"id": "A", "text": "The query engine satisfies the query entirely from index leaf pages without fetching table heap pages"},
            {"id": "B", "text": "An operation where the database drops all secondary indexes during writes"},
            {"id": "C", "text": "A full table scan that ignores all primary keys"},
            {"id": "D", "text": "A join performed entirely inside GPU memory"},
        ],
        "correct_option_id": "A",
        "explanation": "When all projected columns and filter conditions are present within the index key and included attributes, the engine reads directly from the index without reading the heap table, drastically saving I/O.",
    },
    {
        "subject_slug": "dbms",
        "topic_slug": "indexing-and-query-opt",
        "subtopic_slug": "hash-index",
        "difficulty": "easy",
        "prompt_text": "What type of SQL comparison predicate can a Hash Index efficiently evaluate?",
        "options": [
            {"id": "A", "text": "Exact equality comparisons (WHERE col = value)"},
            {"id": "B", "text": "Range comparisons (WHERE col BETWEEN 10 AND 20)"},
            {"id": "C", "text": "Prefix pattern matching (WHERE col LIKE 'abc%')"},
            {"id": "D", "text": "Sorted pagination (ORDER BY col)"},
        ],
        "correct_option_id": "A",
        "explanation": "Hash indexes map values through a hash function with O(1) equality lookup, but destroy order, making them unsuitable for range searches or ORDER BY operations.",
    },

    # =========================================================================
    # 7. DBMS: transactions-and-acid
    # =========================================================================
    {
        "subject_slug": "dbms",
        "topic_slug": "transactions-and-acid",
        "subtopic_slug": "acid-properties",
        "difficulty": "easy",
        "prompt_text": "Which ACID property guarantees that all operations within a transaction succeed together or are rolled back completely?",
        "options": [
            {"id": "A", "text": "Atomicity"},
            {"id": "B", "text": "Consistency"},
            {"id": "C", "text": "Isolation"},
            {"id": "D", "text": "Durability"},
        ],
        "correct_option_id": "A",
        "explanation": "Atomicity guarantees the 'all-or-nothing' execution property: if any operation fails, all changes made by the transaction are rolled back.",
    },
    {
        "subject_slug": "dbms",
        "topic_slug": "transactions-and-acid",
        "subtopic_slug": "isolation-levels",
        "difficulty": "medium",
        "prompt_text": "Which transaction isolation anomaly is prevented by REPEATABLE READ but permitted under READ COMMITTED?",
        "options": [
            {"id": "A", "text": "Non-Repeatable Read (Fuzzy Read)"},
            {"id": "B", "text": "Dirty Read"},
            {"id": "C", "text": "Dirty Write"},
            {"id": "D", "text": "Lost Update under strict 2PL"},
        ],
        "correct_option_id": "A",
        "explanation": "READ COMMITTED allows another committed transaction to modify a row between two reads, causing different values (non-repeatable read). REPEATABLE READ holds shared locks or uses MVCC snapshots to prevent this.",
    },
    {
        "subject_slug": "dbms",
        "topic_slug": "transactions-and-acid",
        "subtopic_slug": "wal-recovery",
        "difficulty": "hard",
        "prompt_text": "Under the Write-Ahead Logging (WAL) protocol, what rule must be strictly enforced before dirty data pages are flushed to disk?",
        "options": [
            {"id": "A", "text": "The log record describing the update must be written and flushed to durable storage first"},
            {"id": "B", "text": "All concurrent transactions must first be aborted"},
            {"id": "C", "text": "The database must perform a complete checkpoint"},
            {"id": "D", "text": "The client connection must be terminated"},
        ],
        "correct_option_id": "A",
        "explanation": "The core WAL protocol dictates that the log record corresponding to an update must be flushed to non-volatile disk before the modified data page can be written, guaranteeing atomicity and durability via UNDO/REDO.",
    },
    {
        "subject_slug": "dbms",
        "topic_slug": "transactions-and-acid",
        "subtopic_slug": "durability",
        "difficulty": "easy",
        "prompt_text": "Which mechanism ensures Durability in relational databases in the event of an abrupt system power loss after COMMIT?",
        "options": [
            {"id": "A", "text": "Sequential Write-Ahead Logging (WAL) / Redo log fsync"},
            {"id": "B", "text": "In-memory LRU cache discard"},
            {"id": "C", "text": "Automatic table truncation"},
            {"id": "D", "text": "Re-reading queries from client history"},
        ],
        "correct_option_id": "A",
        "explanation": "Committing a transaction requires forcing its redo log entries to persistent disk via synchronous fsync, ensuring durability across unexpected crashes.",
    },

    # =========================================================================
    # 8. DBMS: concurrency-and-recovery
    # =========================================================================
    {
        "subject_slug": "dbms",
        "topic_slug": "concurrency-and-recovery",
        "subtopic_slug": "two-phase-locking",
        "difficulty": "easy",
        "prompt_text": "In Strict Two-Phase Locking (Strict 2PL), when are exclusive (write) locks released?",
        "options": [
            {"id": "A", "text": "At the very end of the transaction upon COMMIT or ROLLBACK"},
            {"id": "B", "text": "Immediately after the write statement finishes"},
            {"id": "C", "text": "During the growing phase"},
            {"id": "D", "text": "When another transaction requests a read lock"},
        ],
        "correct_option_id": "A",
        "explanation": "Strict 2PL prevents cascading aborts by holding all exclusive locks until transaction commit or abort is finalized.",
    },
    {
        "subject_slug": "dbms",
        "topic_slug": "concurrency-and-recovery",
        "subtopic_slug": "mvcc",
        "difficulty": "medium",
        "prompt_text": "How does Multi-Version Concurrency Control (MVCC) eliminate read/write lock contention in high-throughput engines like PostgreSQL?",
        "options": [
            {"id": "A", "text": "Readers do not block writers, and writers do not block readers; readers view a consistent snapshot"},
            {"id": "B", "text": "MVCC converts all tables into single-threaded read-only views"},
            {"id": "C", "text": "MVCC drops all index constraints during concurrent queries"},
            {"id": "D", "text": "MVCC routes all transactions to separate physical disks"},
        ],
        "correct_option_id": "A",
        "explanation": "MVCC maintains multiple timestamped versions of tuple rows. A query reads the version visible at its snapshot creation time without acquiring read locks, allowing concurrent non-conflicting writes.",
    },
    {
        "subject_slug": "dbms",
        "topic_slug": "concurrency-and-recovery",
        "subtopic_slug": "deadlock-detection",
        "difficulty": "hard",
        "prompt_text": "How does an engine detecting deadlocks through a Wait-For Graph (WFG) identify that a deadlock has occurred?",
        "options": [
            {"id": "A", "text": "By detecting a directed cycle in the Wait-For Graph"},
            {"id": "B", "text": "When CPU utilization hits 100%"},
            {"id": "C", "text": "When a single transaction holds more than 100 shared locks"},
            {"id": "D", "text": "When the connection pool is exhausted"},
        ],
        "correct_option_id": "A",
        "explanation": "In a Wait-For Graph where directed edges point from waiting transactions to the transactions holding the contested locks, a directed cycle represents a circular wait condition (deadlock).",
    },
    {
        "subject_slug": "dbms",
        "topic_slug": "concurrency-and-recovery",
        "subtopic_slug": "optimistic-concurrency",
        "difficulty": "medium",
        "prompt_text": "In Optimistic Concurrency Control (OCC), when does validation check for conflict against concurrent transactions?",
        "options": [
            {"id": "A", "text": "During the validation phase right before write commit"},
            {"id": "B", "text": "At every SELECT query"},
            {"id": "C", "text": "Before acquiring memory buffers"},
            {"id": "D", "text": "Only when the server reboots"},
        ],
        "correct_option_id": "A",
        "explanation": "OCC assumes conflicts are rare. Transactions execute without locks during the read phase and perform serializability checks in the validation phase just prior to writing commit updates.",
    },
]


async def seed_canonical_question_bank() -> int:
    """
    Seeds the MongoDB questions collection with canonical, approved questions if empty.
    Returns the count of seeded questions.
    """
    existing_count = await Question.count()
    if existing_count >= len(SEED_QUESTIONS):
        logger.info("Question bank already populated (%d questions exist).", existing_count)
        return existing_count

    inserted = 0
    for q_data in SEED_QUESTIONS:
        # Check if question with same prompt already exists
        exists = await Question.find_one(
            Question.subject_slug == q_data["subject_slug"],
            Question.prompt_text == q_data["prompt_text"],
        )
        if not exists:
            options = [QuestionOption(id=opt["id"], text=opt["text"]) for opt in q_data["options"]]
            question = Question(
                subject_slug=q_data["subject_slug"],
                topic_slug=q_data["topic_slug"],
                subtopic_slug=q_data["subtopic_slug"],
                difficulty=q_data["difficulty"],
                prompt_text=q_data["prompt_text"],
                code_snippet=q_data.get("code_snippet"),
                options=options,
                correct_option_id=q_data["correct_option_id"],
                explanation=q_data["explanation"],
                review_status="approved",
                reviewed_by="system_curator",
                reviewed_at=datetime.now(timezone.utc),
            )
            await question.insert()
            inserted += 1

    logger.info("Successfully seeded %d canonical questions into question bank.", inserted)
    return await Question.count()
