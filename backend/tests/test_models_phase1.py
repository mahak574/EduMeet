import pytest
from app.models.consolidated import User, validate_slug, Match, MatchParty
from pydantic import ValidationError


def test_slug_validation_success():
    assert validate_slug("dbms") == "dbms"
    assert validate_slug("operating-systems") == "operating-systems"
    assert validate_slug("data_structures_1") == "data_structures_1"


def test_slug_validation_failure():
    with pytest.raises(ValueError):
        validate_slug("dbms.transactions")  # Periods are forbidden to prevent MongoDB dict key issues

    with pytest.raises(ValueError):
        validate_slug("DSA & Graphs!")


def test_user_model_role_and_defaults():
    user = User(
        email="learner@example.org",
        full_name="Sarah Connor",
        role="student",
        age_confirmed=True,
        country="US",
        timezone="America/Los_Angeles",
        subjects_studied=["dsa", "dbms"],
    )
    assert user.role == "student"
    assert user.age_confirmed is True
    assert user.country == "US"
    assert "dsa" in user.subjects_studied


def test_user_model_admin_role():
    admin = User(
        email="admin@edumeet.org",
        full_name="Platform Admin",
        role="admin",
        age_confirmed=True,
        country="US",
    )
    assert admin.role == "admin"


def test_match_participants_must_be_exactly_two():
    with pytest.raises(ValidationError):
        # 1 participant should fail validation (min_length=2, max_length=2)
        Match(
            participants=[
                MatchParty(
                    user_id="6713cf8e2c39a2b5e4f1a001",
                    teach_subject_slug="dsa",
                    teach_topic_slug="trees",
                    learn_subject_slug="dbms",
                    learn_topic_slug="sql",
                )
            ],
            score=0.9,
            common_languages=["en"],
            proposed_slots=[],
            expires_at="2026-10-25T12:00:00Z",
        )


def test_session_lifecycle_status_and_attendance():
    from app.models.consolidated import Session, SessionParticipant
    from beanie import PydanticObjectId

    p1 = SessionParticipant(
        user_id=PydanticObjectId(),
        role="teacher_a",
        teach_subject_slug="dsa",
        teach_topic_slug="arrays",
        learn_subject_slug="dbms",
        learn_topic_slug="indexing",
    )
    p2 = SessionParticipant(
        user_id=PydanticObjectId(),
        role="teacher_b",
        teach_subject_slug="dbms",
        teach_topic_slug="indexing",
        learn_subject_slug="dsa",
        learn_topic_slug="arrays",
    )

    session = Session(
        match_id=PydanticObjectId(),
        status="waiting_room",
        scheduled_start_utc="2026-10-25T12:00:00Z",
        scheduled_end_utc="2026-10-25T13:00:00Z",
        video_room_id="room_123",
        yjs_doc_id="doc_123",
        participants=[p1, p2],
        present_user_ids=[p1.user_id],
    )
    assert session.status == "waiting_room"
    assert session.disconnect_grace_seconds == 180
    assert session.max_pause_cap_seconds == 600
    assert len(session.present_user_ids) == 1

    # Transition to teacher_a
    session.status = "teacher_a"
    assert session.status == "teacher_a"

    # Transition to no_show_cancelled
    session.status = "no_show_cancelled"
    assert session.status == "no_show_cancelled"


def test_quiz_attempt_resumes_and_served_questions():
    from app.models.consolidated import QuizAttempt
    from beanie import PydanticObjectId

    attempt = QuizAttempt(
        user_id=PydanticObjectId(),
        subject_slug="dsa",
        attempt_number=1,
        assigned_question_ids=[PydanticObjectId()],
    )
    assert attempt.resume_count == 0
    assert attempt.max_resumes == 2
    assert attempt.expires_at > attempt.started_at
    assert isinstance(attempt.served_question_ids, list)

