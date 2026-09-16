"""Authentication Service - JWT & Password Management"""
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict
import jwt
import hashlib
from app.config import settings
from app.database import SessionLocal
from app.models import User

logger = logging.getLogger(__name__)

# Password hashing - use SHA256 for development due to bcrypt compatibility issues
class PasswordHasher:
    """Simple password hasher using SHA256 (fallback for bcrypt issues)"""

    @staticmethod
    def hash(password: str) -> str:
        """Hash password using SHA256"""
        return hashlib.sha256(password.encode()).hexdigest()

    @staticmethod
    def verify(password: str, hash_str: str) -> bool:
        """Verify password against hash"""
        return PasswordHasher.hash(password) == hash_str

pwd_context = PasswordHasher()


class AuthService:
    """Service for authentication operations"""

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password using SHA256"""
        return hashlib.sha256(password.encode()).hexdigest()

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        return AuthService.hash_password(plain_password) == hashed_password

    @staticmethod
    def create_access_token(user_id: str, email: str) -> str:
        """
        Create JWT access token

        Args:
            user_id: User ID
            email: User email

        Returns:
            JWT token string
        """
        expires = datetime.utcnow() + timedelta(
            minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
        )
        payload = {
            "sub": str(user_id),
            "email": email,
            "type": "access",
            "exp": expires,
            "iat": datetime.utcnow(),
        }
        token = jwt.encode(
            payload,
            settings.JWT_SECRET,
            algorithm=settings.JWT_ALGORITHM,
        )
        logger.info(f"Access token created for user: {email}")
        return token

    @staticmethod
    def create_refresh_token(user_id: str, email: str) -> str:
        """
        Create JWT refresh token

        Args:
            user_id: User ID
            email: User email

        Returns:
            JWT refresh token string
        """
        expires = datetime.utcnow() + timedelta(
            days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS
        )
        payload = {
            "sub": str(user_id),
            "email": email,
            "type": "refresh",
            "exp": expires,
            "iat": datetime.utcnow(),
        }
        token = jwt.encode(
            payload,
            settings.JWT_SECRET,
            algorithm=settings.JWT_ALGORITHM,
        )
        logger.info(f"Refresh token created for user: {email}")
        return token

    @staticmethod
    def verify_token(token: str) -> Optional[Dict]:
        """
        Verify JWT token

        Args:
            token: JWT token string

        Returns:
            Decoded payload if valid, None if invalid
        """
        try:
            payload = jwt.decode(
                token,
                settings.JWT_SECRET,
                algorithms=[settings.JWT_ALGORITHM],
            )
            user_id = payload.get("sub")
            email = payload.get("email")
            if user_id and email:
                return {
                    "user_id": user_id,
                    "email": email,
                    "type": payload.get("type"),
                }
            return None
        except jwt.ExpiredSignatureError:
            logger.warning("Token expired")
            return None
        except jwt.InvalidTokenError:
            logger.warning("Invalid token")
            return None

    @staticmethod
    def register_user(email: str, password: str, full_name: str = None) -> Optional[Dict]:
        """
        Register new user

        Args:
            email: User email
            password: Plain text password
            full_name: User's full name

        Returns:
            User data dict if successful, None if user exists
        """
        db = SessionLocal()
        try:
            # Check if user exists
            existing_user = db.query(User).filter(User.email == email).first()
            if existing_user:
                logger.warning(f"User already exists: {email}")
                return None

            # Hash password
            hashed_password = AuthService.hash_password(password)

            # Create new user
            from uuid import uuid4
            user = User(
                id=uuid4(),
                email=email,
                password_hash=hashed_password,
                full_name=full_name,
                role="recruiter",
                is_active=True,
            )
            db.add(user)
            db.commit()
            db.refresh(user)

            logger.info(f"User registered: {email}")

            return {
                "id": str(user.id),
                "email": user.email,
                "full_name": user.full_name,
                "role": user.role,
            }

        except Exception as e:
            db.rollback()
            logger.error(f"User registration error: {e}")
            return None
        finally:
            db.close()

    @staticmethod
    def authenticate_user(email: str, password: str) -> Optional[Dict]:
        """
        Authenticate user and return tokens

        Args:
            email: User email
            password: Plain text password

        Returns:
            Dict with user data and tokens if successful
        """
        db = SessionLocal()
        try:
            # Find user
            user = db.query(User).filter(User.email == email).first()
            if not user:
                logger.warning(f"User not found: {email}")
                return None

            # Check if active
            if not user.is_active:
                logger.warning(f"User inactive: {email}")
                return None

            # Verify password
            if not AuthService.verify_password(password, user.password_hash):
                logger.warning(f"Invalid password for user: {email}")
                return None

            # Generate tokens
            access_token = AuthService.create_access_token(str(user.id), user.email)
            refresh_token = AuthService.create_refresh_token(str(user.id), user.email)

            logger.info(f"User authenticated: {email}")

            return {
                "user": {
                    "id": str(user.id),
                    "email": user.email,
                    "full_name": user.full_name,
                    "company_name": user.company_name,
                    "role": user.role,
                },
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "bearer",
            }

        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return None
        finally:
            db.close()

    @staticmethod
    def refresh_access_token(refresh_token: str) -> Optional[str]:
        """
        Generate new access token from refresh token

        Args:
            refresh_token: Refresh token string

        Returns:
            New access token if valid
        """
        payload = AuthService.verify_token(refresh_token)
        if not payload or payload.get("type") != "refresh":
            logger.warning("Invalid refresh token")
            return None

        user_id = payload.get("user_id")
        email = payload.get("email")

        new_access_token = AuthService.create_access_token(user_id, email)
        logger.info(f"Access token refreshed for user: {email}")

        return new_access_token


# Create singleton instance
auth_service = AuthService()
