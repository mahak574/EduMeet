import math
from datetime import datetime, timedelta, timezone
import pytest
from beanie import PydanticObjectId

from app.models.consolidated import (
    Availability,
    Match,
    MatchingPoolEntry,
    RecurringLocalSlot,
    Session,
    SkillProfile,
    TopicSkill,
    User,
    UserPreferences,
)
from app.services.matching_service import MatchingService


@pytest.mark.asyncio
async def test_calculate_topic_gain():
    """Validates reciprocal knowledge gain formula with edge cases."""
    # Strong teacher (90) teaching learner with gap (30)
    # Gap = 80 - 30 = 50; Advantage = 90 - 60 = 30
    # Gain = (50 * 30) / 3200 = 1500 / 3200 = 0.46875 -> 0.4688
    gain = MatchingService.calculate_topic_gain(teacher_score=90.0, learner_score=30.0)
    assert abs(gain - 0.4688) < 0.001

    # Teacher below threshold (55 <= 60) -> Gain must be 0
    zero_teacher = MatchingService.calculate_topic_gain(teacher_score=55.0, learner_score=20.0)
    assert zero_teacher == 0.0

    # Learner above threshold (85 >= 80) -> Gain must be 0
    zero_learner = MatchingService.calculate_topic_gain(teacher_score=95.0, learner_score=85.0)
    assert zero_learner == 0.0


@pytest.mark.asyncio
async def test_optimal_topic_pair_selection():
    """Validates cross-topic pairing selection with reciprocal bottleneck."""
    now = datetime.now(timezone.utc)
    user_a_id = PydanticObjectId()
    user_b_id = PydanticObjectId()

    # User A: strong in arrays (85), weak in dp (35)
    prof_a = SkillProfile(
        user_id=user_a_id,
        subjects={
            "dsa": {
                "arrays-and-hashing": TopicSkill(overall_score=85.0),
                "dynamic-programming": TopicSkill(overall_score=35.0),
            }
        },
    )

    # User B: weak in arrays (40), strong in dp (90)
    prof_b = SkillProfile(
        user_id=user_b_id,
        subjects={
            "dsa": {
                "arrays-and-hashing": TopicSkill(overall_score=40.0),
                "dynamic-programming": TopicSkill(overall_score=90.0),
            }
        },
    )

    pair = MatchingService.find_optimal_topic_pair(prof_a, prof_b, ["dsa"])
    assert pair is not None
    subj_a, topic_a, subj_b, topic_b, gain = pair

    assert subj_a == "dsa"
    assert topic_a == "arrays-and-hashing"  # A teaches arrays
    assert topic_b == "dynamic-programming"  # B teaches DP
    assert gain > 0.0


@pytest.mark.asyncio
async def test_no_show_penalty_degradation():
    """Validates that no_show_count degrades edge weights exponentially."""
    now = datetime.now(timezone.utc)
    u_good = User(
        email="reliable@example.com",
        full_name="Reliable Student",
        age_confirmed=True,
        country="US",
        timezone="UTC",
        languages=["en"],
        no_show_count=0,
    )
    u_flaky = User(
        email="flaky@example.com",
        full_name="Flaky Student",
        age_confirmed=True,
        country="US",
        timezone="UTC",
        languages=["en"],
        no_show_count=3,
    )
    await u_good.insert()
    await u_flaky.insert()

    prof_good = SkillProfile(
        user_id=u_good.id,
        subjects={
            "dsa": {
                "arrays-and-hashing": TopicSkill(overall_score=85.0),
                "dynamic-programming": TopicSkill(overall_score=35.0),
            }
        },
    )
    prof_flaky = SkillProfile(
        user_id=u_flaky.id,
        subjects={
            "dsa": {
                "arrays-and-hashing": TopicSkill(overall_score=35.0),
                "dynamic-programming": TopicSkill(overall_score=85.0),
            }
        },
    )
    await prof_good.insert()
    await prof_flaky.insert()

    avail = Availability(
        user_id=u_good.id,
        timezone="UTC",
        weekly_slots=[RecurringLocalSlot(day_of_week=i, start_min=1080, end_min=1200) for i in range(7)],
    )
    await avail.insert()

    # Flaky pair has total 3 no-shows -> weight should be scaled by e^(-0.5 * 3) = e^(-1.5) ~= 0.2231
    res = await MatchingService.compute_pair_weight(
        user_a=u_good,
        user_b=u_flaky,
        profile_a=prof_good,
        profile_b=prof_flaky,
        avail_a=avail,
        avail_b=avail,
        common_subjects=["dsa"],
    )
    assert res is not None
    weight, details = res
    raw_gain = details["raw_gain"]

    # The reliability penalty should significantly decrease the weight
    expected_penalty = math.exp(-0.5 * 3)
    assert weight < raw_gain
    assert weight <= raw_gain * 1.5 * expected_penalty


@pytest.mark.asyncio
async def test_networkx_max_weight_matching_lifecycle():
    """Sets up pool entries and tests NetworkX global max weight matching."""
    now = datetime.now(timezone.utc)

    # Clean pool for test
    await MatchingPoolEntry.find().delete()
    await Match.find().delete()

    # Create 4 students with complementary profiles: (1 and 2 match, 3 and 4 match)
    users = []
    profiles = []
    for i in range(4):
        u = User(
            email=f"student_{i}@example.com",
            full_name=f"Student {i}",
            age_confirmed=True,
            country="US",
            timezone="UTC",
            languages=["en"],
        )
        await u.insert()
        users.append(u)

        # 0 and 1 are complementary in arrays vs dp
        # 2 and 3 are complementary in trees vs linked-lists
        if i == 0:
            p = SkillProfile(
                user_id=u.id,
                subjects={
                    "dsa": {
                        "arrays-and-hashing": TopicSkill(overall_score=90.0),
                        "dynamic-programming": TopicSkill(overall_score=30.0),
                    }
                },
            )
        elif i == 1:
            p = SkillProfile(
                user_id=u.id,
                subjects={
                    "dsa": {
                        "arrays-and-hashing": TopicSkill(overall_score=35.0),
                        "dynamic-programming": TopicSkill(overall_score=85.0),
                    }
                },
            )
        elif i == 2:
            p = SkillProfile(
                user_id=u.id,
                subjects={
                    "dsa": {
                        "trees-and-graphs": TopicSkill(overall_score=85.0),
                        "linked-lists-and-stacks": TopicSkill(overall_score=30.0),
                    }
                },
            )
        else:
            p = SkillProfile(
                user_id=u.id,
                subjects={
                    "dsa": {
                        "trees-and-graphs": TopicSkill(overall_score=40.0),
                        "linked-lists-and-stacks": TopicSkill(overall_score=90.0),
                    }
                },
            )
        await p.insert()
        profiles.append(p)

        # Enter each into pool
        entry = MatchingPoolEntry(
            user_id=u.id,
            subject_slugs=["dsa"],
            status="active",
        )
        await entry.insert()

    # Run matching cycle
    created_matches = await MatchingService.run_matching_cycle()
    assert len(created_matches) == 2  # 4 students -> 2 disjoint 1:1 pairs

    # Verify all pool entries are now matched
    for u in users:
        p_entry = await MatchingService.get_pool_status(u.id)
        assert p_entry.status == "matched"
        assert p_entry.current_match_id is not None


@pytest.mark.asyncio
async def test_mutual_confirmation_and_session_creation():
    """Validates 2-party confirmation and atomic session scheduling."""
    now = datetime.now(timezone.utc)
    u1 = User(
        email="conf1@example.com",
        full_name="User One",
        age_confirmed=True,
        country="US",
        timezone="UTC",
        languages=["en"],
    )
    u2 = User(
        email="conf2@example.com",
        full_name="User Two",
        age_confirmed=True,
        country="US",
        timezone="UTC",
        languages=["en"],
    )
    await u1.insert()
    await u2.insert()

    proposed_slot = now + timedelta(days=2, hours=14)
    from app.models.consolidated import MatchParty

    match = Match(
        participants=[
            MatchParty(
                user_id=u1.id,
                teach_subject_slug="dsa",
                teach_topic_slug="arrays-and-hashing",
                learn_subject_slug="dsa",
                learn_topic_slug="dynamic-programming",
            ),
            MatchParty(
                user_id=u2.id,
                teach_subject_slug="dsa",
                teach_topic_slug="dynamic-programming",
                learn_subject_slug="dsa",
                learn_topic_slug="arrays-and-hashing",
            ),
        ],
        score=0.45,
        common_languages=["en"],
        proposed_slots=[proposed_slot],
        status="pending",
        expires_at=now + timedelta(hours=24),
    )
    await match.insert()

    # User 1 confirms
    m1, sess1 = await MatchingService.confirm_match(u1.id, match.id, proposed_slot)
    assert m1.status == "pending"
    assert sess1 is None
    assert m1.participants[0].confirmed is True

    # User 2 confirms -> mutual confirmation triggers session creation
    m2, sess2 = await MatchingService.confirm_match(u2.id, match.id, proposed_slot)
    assert m2.status == "confirmed"
    assert sess2 is not None
    assert sess2.status == "scheduled"
    assert sess2.match_id == match.id
    assert len(sess2.participants) == 2
    assert sess2.participants[0].role == "teacher_a"
    assert sess2.participants[1].role == "teacher_b"


@pytest.mark.asyncio
async def test_match_decline_restores_partner():
    """Declining a match rejects it and returns the non-declining user to the active pool."""
    now = datetime.now(timezone.utc)
    u1 = User(
        email="dec1@example.com",
        full_name="Dec One",
        age_confirmed=True,
        country="US",
        timezone="UTC",
        languages=["en"],
    )
    u2 = User(
        email="dec2@example.com",
        full_name="Dec Two",
        age_confirmed=True,
        country="US",
        timezone="UTC",
        languages=["en"],
    )
    await u1.insert()
    await u2.insert()

    pool1 = MatchingPoolEntry(user_id=u1.id, status="matched")
    pool2 = MatchingPoolEntry(user_id=u2.id, status="matched")
    await pool1.insert()
    await pool2.insert()

    from app.models.consolidated import MatchParty

    match = Match(
        participants=[
            MatchParty(
                user_id=u1.id,
                teach_subject_slug="dsa",
                teach_topic_slug="arrays-and-hashing",
                learn_subject_slug="dsa",
                learn_topic_slug="dynamic-programming",
            ),
            MatchParty(
                user_id=u2.id,
                teach_subject_slug="dsa",
                teach_topic_slug="dynamic-programming",
                learn_subject_slug="dsa",
                learn_topic_slug="arrays-and-hashing",
            ),
        ],
        score=0.42,
        common_languages=["en"],
        proposed_slots=[now + timedelta(days=1)],
        status="pending",
        expires_at=now + timedelta(hours=24),
    )
    await match.insert()

    # User 1 declines
    success = await MatchingService.decline_match(u1.id, match.id, "Scheduling conflict")
    assert success is True

    # User 1's entry is cancelled, User 2's entry is restored to active
    p1_after = await MatchingPoolEntry.find_one(MatchingPoolEntry.user_id == u1.id)
    p2_after = await MatchingPoolEntry.find_one(MatchingPoolEntry.user_id == u2.id)

    assert p1_after.status == "cancelled"
    assert p2_after.status == "active"
    assert p2_after.current_match_id is None


@pytest.mark.asyncio
async def test_join_pool_with_subject_slugs():
    """Validates that join_pool validates slug and adds user to pool."""
    user = User(
        email="pooljoiner@example.com",
        full_name="Pool Joiner",
        age_confirmed=True,
        country="US",
        timezone="UTC",
    )
    await user.insert()

    profile = SkillProfile(
        user_id=user.id,
        subjects={
            "dsa": {"arrays": TopicSkill(overall_score=75.0)},
        },
    )
    await profile.insert()

    entry = await MatchingService.join_pool(user.id, subject_slugs=["dsa", "python"])
    assert entry is not None
    assert entry.status == "active"
    assert "dsa" in entry.subject_slugs
    assert "python" in entry.subject_slugs

