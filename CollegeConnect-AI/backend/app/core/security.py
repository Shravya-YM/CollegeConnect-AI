import secrets
from fastapi import Header, HTTPException, status
from app.core.config import settings

def verify_admin_key(x_admin_api_key: str = Header(None, alias="X-Admin-API-Key")) -> bool:
    """
    Validates admin API key using constant-time comparison to prevent timing attacks.
    """
    if not x_admin_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing required 'X-Admin-API-Key' header.",
            headers={"WWW-Authenticate": "ApiKey"}
        )

    # Constant time string comparison
    is_valid = secrets.compare_digest(x_admin_api_key, settings.ADMIN_API_KEY)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Admin API Key.",
            headers={"WWW-Authenticate": "ApiKey"}
        )
    return True
