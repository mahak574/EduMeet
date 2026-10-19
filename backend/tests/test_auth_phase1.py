import pytest
from app.core.security import (
    compute_otp_hmac,
    verify_otp_hmac,
    generate_numeric_otp,
    create_access_token,
    decode_access_token,
    generate_refresh_token,
    hash_refresh_token,
)


def test_numeric_otp_generation():
    otp = generate_numeric_otp(6)
    assert len(otp) == 6
    assert otp.isdigit()


def test_hmac_otp_matching():
    email = "Student@Example.Org"
    code = "481920"
    digest = compute_otp_hmac(email, code)

    # Should match even if email casing varies because of normalization
    assert verify_otp_hmac("student@example.org", code, digest) is True
    assert verify_otp_hmac("STUDENT@EXAMPLE.ORG", code, digest) is True

    # Should fail with incorrect code
    assert verify_otp_hmac(email, "999999", digest) is False


def test_access_token_creation_and_decoding():
    user_id = "6713cf8e2c39a2b5e4f1a001"
    token = create_access_token(user_id=user_id, role="student", is_verified_student=True)
    payload = decode_access_token(token)
    assert payload is not None
    assert payload["sub"] == user_id
    assert payload["role"] == "student"
    assert payload["is_verified"] is True
    assert payload["type"] == "access"


def test_refresh_token_hashing():
    raw_token, token_hash = generate_refresh_token()
    assert len(raw_token) > 30
    assert hash_refresh_token(raw_token) == token_hash
