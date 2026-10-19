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
