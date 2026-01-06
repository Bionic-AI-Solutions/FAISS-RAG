"""
Utility functions for hashing API keys and passwords.
"""

import hashlib

import bcrypt

from app.config.auth import auth_settings


def hash_api_key(api_key: str) -> str:
    """
    Hash an API key using bcrypt.
    
    API keys can be longer than bcrypt's 72-byte limit, so we:
    1. First hash with SHA-256 to get a fixed-length value (64 hex chars = 32 bytes)
    2. Then hash that with bcrypt for secure storage
    
    Args:
        api_key: Plain text API key
        
    Returns:
        str: Bcrypt-hashed API key (as string)
    """
    # First, hash with SHA-256 to get fixed-length value (64 hex characters)
    # This ensures we stay within bcrypt's 72-byte limit
    sha256_hash = hashlib.sha256(api_key.encode("utf-8")).hexdigest()
    
    # Then hash with bcrypt for secure storage
    # bcrypt.hashpw returns bytes, so we decode to string for storage
    hashed = bcrypt.hashpw(sha256_hash.encode("utf-8"), bcrypt.gensalt())
    return hashed.decode("utf-8")


def verify_api_key(plain_key: str, hashed_key: str) -> bool:
    """
    Verify an API key against its hash.
    
    Args:
        plain_key: Plain text API key to verify
        hashed_key: Bcrypt-hashed API key to verify against
        
    Returns:
        bool: True if keys match, False otherwise
    """
    try:
        # Hash the plain key with SHA-256 first
        sha256_hash = hashlib.sha256(plain_key.encode("utf-8")).hexdigest()
        
        # Then verify against bcrypt hash
        return bcrypt.checkpw(sha256_hash.encode("utf-8"), hashed_key.encode("utf-8"))
    except Exception:
        return False

