"""Authentication & Authorization Middleware"""
import logging
from typing import Optional, List
from fastapi import HTTPException, Depends, Request
from app.services.auth_service import auth_service
from app.database import SessionLocal
from app.models import User

logger = logging.getLogger(__name__)


async def get_current_user(request: Request) -> dict:
    """
    Extract and verify current user from JWT token

    Args:
        request: FastAPI request object

    Returns:
        User data dict with user_id and email
    """
    try:
        # Get authorization header
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            raise HTTPException(status_code=401, detail="Missing authorization header")

        # Extract token from "Bearer <token>"
        try:
            scheme, token = auth_header.split()
            if scheme.lower() != "bearer":
                raise ValueError("Invalid auth scheme")
        except ValueError:
            raise HTTPException(status_code=401, detail="Invalid token format")

        # Verify token
        payload = auth_service.verify_token(token)
        if not payload or payload.get("type") != "access":
            raise HTTPException(status_code=401, detail="Invalid or expired token")

        user_id = payload.get("user_id")
        email = payload.get("email")

        if not user_id or not email:
            raise HTTPException(status_code=401, detail="Invalid token payload")

        logger.info(f"User authenticated: {email}")

        return {
            "user_id": user_id,
            "email": email,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Authentication error: {e}")
        raise HTTPException(status_code=401, detail="Authentication failed")


async def get_current_user_with_role(
    current_user: dict = Depends(get_current_user),
) -> dict:
    """
    Get current user with role information

    Args:
        current_user: Current user dict from get_current_user

    Returns:
        User data with role
    """
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == current_user["user_id"]).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        return {
            "user_id": str(user.id),
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role,
            "is_active": user.is_active,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching user role: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch user info")
    finally:
        db.close()


def check_role(required_roles: List[str]):
    """
    Factory function to create role-checking dependency

    Args:
        required_roles: List of allowed roles (e.g., ["admin", "recruiter"])

    Returns:
        Async function that checks user role
    """
    async def role_checker(current_user: dict = Depends(get_current_user_with_role)):
        if current_user["role"] not in required_roles:
            logger.warning(f"Access denied for user {current_user['email']} - role {current_user['role']}")
            raise HTTPException(
                status_code=403,
                detail=f"Access denied. Required roles: {', '.join(required_roles)}",
            )
        return current_user

    return role_checker


def require_admin(current_user: dict = Depends(check_role(["admin"]))):
    """Require admin role"""
    return current_user


def require_recruiter(current_user: dict = Depends(check_role(["admin", "recruiter"]))):
    """Require admin or recruiter role"""
    return current_user


def require_any_role(current_user: dict = Depends(get_current_user_with_role)):
    """Require any authenticated user"""
    return current_user
