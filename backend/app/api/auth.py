"""Authentication API Endpoints"""
from fastapi import APIRouter, HTTPException, Depends
from app.services.auth_service import auth_service
from app.schemas.auth import (
    UserRegister,
    UserLogin,
    AuthResponse,
    TokenResponse,
    RefreshTokenRequest,
)
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/register", response_model=dict)
async def register(user_data: UserRegister):
    """
    Register new user

    Args:
        user_data: Registration details (email, password, full_name)

    Returns:
        User data without tokens
    """
    try:
        # Register user
        user = auth_service.register_user(
            email=user_data.email,
            password=user_data.password,
            full_name=user_data.full_name,
        )

        if not user:
            raise HTTPException(
                status_code=400,
                detail="Email already registered",
            )

        logger.info(f"User registered: {user_data.email}")

        return {
            "status": "success",
            "message": "User registered successfully",
            "data": user,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration error: {e}")
        raise HTTPException(status_code=500, detail="Registration failed")


@router.post("/login", response_model=dict)
async def login(credentials: UserLogin):
    """
    Login user and return JWT tokens

    Args:
        credentials: Email and password

    Returns:
        User data with access and refresh tokens
    """
    try:
        # Authenticate user
        auth_data = auth_service.authenticate_user(
            email=credentials.email,
            password=credentials.password,
        )

        if not auth_data:
            raise HTTPException(
                status_code=401,
                detail="Invalid email or password",
            )

        logger.info(f"User logged in: {credentials.email}")

        return {
            "status": "success",
            "message": "Login successful",
            "data": auth_data,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(status_code=500, detail="Login failed")


@router.post("/refresh", response_model=dict)
async def refresh_token(request: RefreshTokenRequest):
    """
    Refresh access token using refresh token

    Args:
        request: Contains refresh token

    Returns:
        New access token
    """
    try:
        # Refresh access token
        new_access_token = auth_service.refresh_access_token(
            refresh_token=request.refresh_token
        )

        if not new_access_token:
            raise HTTPException(
                status_code=401,
                detail="Invalid or expired refresh token",
            )

        logger.info("Access token refreshed")

        return {
            "status": "success",
            "data": {
                "access_token": new_access_token,
                "token_type": "bearer",
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token refresh error: {e}")
        raise HTTPException(status_code=500, detail="Token refresh failed")


@router.get("/me", response_model=dict)
async def get_current_user(authorization: str = None):
    """
    Get current user info from token

    Args:
        authorization: Bearer token header

    Returns:
        Current user data
    """
    try:
        if not authorization:
            raise HTTPException(status_code=401, detail="Missing token")

        # Extract token from "Bearer <token>"
        try:
            scheme, token = authorization.split()
            if scheme.lower() != "bearer":
                raise ValueError("Invalid auth scheme")
        except ValueError:
            raise HTTPException(status_code=401, detail="Invalid token format")

        # Verify token
        payload = auth_service.verify_token(token)
        if not payload or payload.get("type") != "access":
            raise HTTPException(status_code=401, detail="Invalid token")

        logger.info(f"Current user retrieved: {payload.get('email')}")

        return {
            "status": "success",
            "data": {
                "user_id": payload.get("user_id"),
                "email": payload.get("email"),
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get current user error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get user info")
