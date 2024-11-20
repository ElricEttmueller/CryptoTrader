import pytest
from auth.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    verify_token
)

def test_password_hashing():
    """Test password hashing and verification"""
    password = "testpassword123"
    hashed = get_password_hash(password)
    
    # Verify the hash works
    assert verify_password(password, hashed)
    
    # Verify wrong password fails
    assert not verify_password("wrongpassword", hashed)

def test_token_creation_and_verification():
    """Test JWT token creation and verification"""
    user_data = {"sub": "test@example.com"}
    token = create_access_token(user_data)
    
    # Verify token can be decoded
    decoded = verify_token(token)
    assert decoded["sub"] == user_data["sub"]
    
    # Verify invalid token fails
    with pytest.raises(Exception):
        verify_token("invalid.token.here")

def test_token_expiration():
    """Test token expiration"""
    from datetime import datetime, timedelta
    user_data = {
        "sub": "test@example.com",
        "exp": datetime.utcnow() - timedelta(minutes=1)
    }
    token = create_access_token(user_data)
    
    # Verify expired token fails
    with pytest.raises(Exception):
        verify_token(token)
