"""User Management API Endpoints"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
import logging

from app.database import get_db
from app.models import User
from app.middleware.auth_middleware import (
    get_current_user_with_role,
    check_role,
)

router = APIRouter()
logger = logging.getLogger(__name__)


class UpdateUserRoleRequest(BaseModel):
    """Update user role request"""
    role: str  # admin, recruiter, viewer


@router.get("/users")
async def list_users(
    skip: int = 0,
    limit: int = 50,
    current_user: dict = Depends(check_role(["admin"])),
    db: Session = Depends(get_db),
):
    """
    List all users (admin only)

    Args:
        skip: Pagination offset
        limit: Pagination limit
        current_user: Current authenticated admin user

    Returns:
        List of users
    """
    try:
        users = db.query(User).offset(skip).limit(limit).all()

        return {
            "status": "success",
            "data": [
                {
                    "id": str(u.id),
                    "email": u.email,
                    "full_name": u.full_name,
                    "company_name": u.company_name,
                    "role": u.role,
                    "is_active": u.is_active,
                    "created_at": u.created_at.isoformat() if u.created_at else None,
                }
                for u in users
            ],
            "total": len(users),
        }

    except Exception as e:
        logger.error(f"List users error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/users/{user_id}")
async def get_user(
    user_id: str,
    current_user: dict = Depends(check_role(["admin"])),
    db: Session = Depends(get_db),
):
    """
    Get user details (admin only)

    Args:
        user_id: User ID to fetch
        current_user: Current authenticated admin user

    Returns:
        User data
    """
    try:
        user = db.query(User).filter(User.id == user_id).first()

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        return {
            "status": "success",
            "data": {
                "id": str(user.id),
                "email": user.email,
                "full_name": user.full_name,
                "company_name": user.company_name,
                "role": user.role,
                "is_active": user.is_active,
                "created_at": user.created_at.isoformat() if user.created_at else None,
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get user error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/users/{user_id}/role")
async def update_user_role(
    user_id: str,
    request: UpdateUserRoleRequest,
    current_user: dict = Depends(check_role(["admin"])),
    db: Session = Depends(get_db),
):
    """
    Update user role (admin only)

    Args:
        user_id: User ID to update
        request: New role
        current_user: Current authenticated admin user

    Returns:
        Updated user data
    """
    try:
        # Validate role
        valid_roles = ["admin", "recruiter", "viewer"]
        if request.role not in valid_roles:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid role. Must be one of: {', '.join(valid_roles)}",
            )

        # Find user
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Prevent demoting the last admin
        if user.role == "admin" and request.role != "admin":
            admin_count = db.query(User).filter(User.role == "admin").count()
            if admin_count == 1:
                raise HTTPException(
                    status_code=400,
                    detail="Cannot demote the last admin user",
                )

        # Update role
        old_role = user.role
        user.role = request.role
        db.commit()
        db.refresh(user)

        logger.info(f"User role updated: {user.email} ({old_role} → {request.role}) by {current_user['email']}")

        return {
            "status": "success",
            "data": {
                "id": str(user.id),
                "email": user.email,
                "role": user.role,
                "message": f"Role updated from {old_role} to {request.role}",
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Update user role error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/users/{user_id}/status")
async def update_user_status(
    user_id: str,
    is_active: bool,
    current_user: dict = Depends(check_role(["admin"])),
    db: Session = Depends(get_db),
):
    """
    Enable/disable user account (admin only)

    Args:
        user_id: User ID to update
        is_active: Active status
        current_user: Current authenticated admin user

    Returns:
        Updated user data
    """
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Prevent disabling the last active admin
        if user.role == "admin" and not is_active:
            active_admins = db.query(User).filter(
                User.role == "admin",
                User.is_active == True,
            ).count()
            if active_admins == 1:
                raise HTTPException(
                    status_code=400,
                    detail="Cannot disable the last active admin",
                )

        user.is_active = is_active
        db.commit()
        db.refresh(user)

        logger.info(f"User status updated: {user.email} (active={is_active}) by {current_user['email']}")

        return {
            "status": "success",
            "data": {
                "id": str(user.id),
                "email": user.email,
                "is_active": user.is_active,
                "message": f"User {'activated' if is_active else 'deactivated'}",
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Update user status error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/profile")
async def get_user_profile(
    current_user: dict = Depends(get_current_user_with_role),
):
    """
    Get current user's profile (any authenticated user)

    Args:
        current_user: Current authenticated user

    Returns:
        User profile data
    """
    return {
        "status": "success",
        "data": current_user,
    }
