from app.core.security import (
    create_access_token,
    decode_token,
    get_password_hash,
    verify_password,
)


def test_password_hash():
    password = "testpassword123"
    hashed = get_password_hash(password)
    assert verify_password(password, hashed)
    assert not verify_password("wrongpassword", hashed)


def test_access_token():
    data = {"sub": "test-user-id", "role": "admin"}
    token = create_access_token(data)
    decoded = decode_token(token)
    assert decoded["sub"] == "test-user-id"
    assert decoded["role"] == "admin"
    assert decoded["type"] == "access"
