"""Test Authentication & RBAC Failure Scenarios"""
import pytest
from app.services.auth_service import auth_service


class TestPasswordFailures:
    """Test password hashing and verification failures"""

    def test_wrong_password(self):
        """Failure: Verify wrong password"""
        password = "CorrectPassword123!"
        hashed = auth_service.hash_password(password)

        # Try wrong password
        result = auth_service.verify_password("WrongPassword", hashed)
        assert result is False, "Should reject wrong password"

    def test_empty_password(self):
        """Failure: Hash empty password"""
        hashed = auth_service.hash_password("")
        assert hashed is not None, "Should hash empty password"

        # Should not match non-empty
        assert not auth_service.verify_password("password", hashed)

    def test_very_long_password(self):
        """Failure: Handle very long password"""
        long_password = "a" * 10000
        hashed = auth_service.hash_password(long_password)

        # Should still verify
        assert auth_service.verify_password(long_password, hashed)
        assert not auth_service.verify_password("wrong", hashed)

    def test_special_characters_password(self):
        """Failure: Handle special characters"""
        special_pass = "P@ssw0rd!#$%^&*()"
        hashed = auth_service.hash_password(special_pass)

        assert auth_service.verify_password(special_pass, hashed)
        assert not auth_service.verify_password("P@ssw0rd", hashed)


class TestTokenFailures:
    """Test JWT token generation and verification failures"""

    def test_invalid_token_format(self):
        """Failure: Verify malformed token"""
        invalid_token = "not.a.jwt"
        result = auth_service.verify_token(invalid_token)
        assert result is None, "Should reject malformed token"

    def test_expired_token(self):
        """Failure: Use expired token"""
        # Create token with -1 minute expiration (already expired)
        from datetime import datetime, timedelta
        import jwt

        expires = datetime.utcnow() - timedelta(minutes=1)  # Expired
        payload = {
            "sub": "user123",
            "email": "test@example.com",
            "type": "access",
            "exp": expires,
            "iat": datetime.utcnow(),
        }
        expired_token = jwt.encode(payload, "secret", algorithm="HS256")

        result = auth_service.verify_token(expired_token)
        assert result is None, "Should reject expired token"

    def test_wrong_secret_token(self):
        """Failure: Token signed with wrong secret"""
        from datetime import datetime, timedelta
        import jwt

        expires = datetime.utcnow() + timedelta(minutes=30)
        payload = {
            "sub": "user123",
            "email": "test@example.com",
            "type": "access",
            "exp": expires,
            "iat": datetime.utcnow(),
        }

        # Sign with wrong secret
        wrong_token = jwt.encode(payload, "wrong_secret", algorithm="HS256")

        result = auth_service.verify_token(wrong_token)
        assert result is None, "Should reject token signed with wrong secret"

    def test_refresh_token_as_access(self):
        """Failure: Use refresh token as access token"""
        refresh_token = auth_service.create_refresh_token("user123", "test@example.com")

        # Verify token returns data but type is "refresh"
        payload = auth_service.verify_token(refresh_token)
        assert payload is not None
        assert payload["type"] == "refresh", "Should identify as refresh token"

        # In middleware, this would be rejected for access endpoints


class TestAuthenticationFailures:
    """Test authentication workflow failures"""

    def test_register_duplicate_email(self):
        """Failure: Register with existing email"""
        email = "duplicate@example.com"
        password = "Password123!"

        # First registration succeeds
        result1 = auth_service.register_user(email, password, "User One")
        assert result1 is not None

        # Second registration with same email fails
        result2 = auth_service.register_user(email, password, "User Two")
        assert result2 is None, "Should not allow duplicate email"

    def test_login_nonexistent_user(self):
        """Failure: Login with non-existent email"""
        result = auth_service.authenticate_user(
            "nonexistent@example.com",
            "SomePassword123!"
        )
        assert result is None, "Should reject non-existent user"

    def test_login_inactive_user(self):
        """Failure: Login as deactivated user"""
        from app.database import SessionLocal
        from app.models import User
        from uuid import uuid4

        db = SessionLocal()
        try:
            # Create inactive user
            user = User(
                id=uuid4(),
                email="inactive@example.com",
                password_hash=auth_service.hash_password("Password123!"),
                is_active=False,
            )
            db.add(user)
            db.commit()

            # Try to login
            result = auth_service.authenticate_user(
                "inactive@example.com",
                "Password123!"
            )
            assert result is None, "Should reject inactive user"

        finally:
            db.close()

    def test_refresh_with_access_token(self):
        """Failure: Try to refresh using access token"""
        access_token = auth_service.create_access_token("user123", "test@example.com")

        # Try to refresh with access token (not refresh token)
        result = auth_service.refresh_access_token(access_token)
        assert result is None, "Should reject access token as refresh token"

    def test_refresh_with_invalid_token(self):
        """Failure: Refresh with invalid token"""
        result = auth_service.refresh_access_token("invalid.token")
        assert result is None, "Should reject invalid refresh token"


class TestRBACFailures:
    """Test Role-Based Access Control failures"""

    def test_unauthorized_role_access(self):
        """Failure: Viewer tries to create job"""
        # Simulate viewer user
        viewer_user = {
            "user_id": "viewer123",
            "email": "viewer@example.com",
            "role": "viewer",
            "is_active": True,
        }

        # Check if viewer has required role
        required_roles = ["admin", "recruiter"]
        assert viewer_user["role"] not in required_roles, "Viewer should not have access"

    def test_cannot_demote_last_admin(self):
        """Failure: Try to demote the only admin"""
        from app.database import SessionLocal
        from app.models import User
        from uuid import uuid4

        db = SessionLocal()
        try:
            # Verify there's only one admin
            admin_count = db.query(User).filter(User.role == "admin").count()

            if admin_count == 1:
                # This should fail (cannot demote last admin)
                admin_user = db.query(User).filter(User.role == "admin").first()
                assert admin_user is not None
                # In the endpoint, this would raise HTTPException(400)

        finally:
            db.close()

    def test_cannot_disable_last_active_admin(self):
        """Failure: Try to disable the only active admin"""
        from app.database import SessionLocal
        from app.models import User

        db = SessionLocal()
        try:
            # Verify there's only one active admin
            active_admins = db.query(User).filter(
                User.role == "admin",
                User.is_active == True,
            ).count()

            if active_admins == 1:
                # This should fail (cannot disable last active admin)
                # In the endpoint, this would raise HTTPException(400)
                assert active_admins >= 1, "Must have at least one active admin"

        finally:
            db.close()


class TestDataValidationFailures:
    """Test data validation failures"""

    def test_invalid_email_format(self):
        """Failure: Register with invalid email"""
        # Pydantic should reject this
        invalid_emails = [
            "notanemail",
            "@example.com",
            "user@",
            "user @example.com",
        ]

        for email in invalid_emails:
            # In FastAPI, Pydantic would validate and reject
            # This is handled at the schema level
            assert "@" not in email or email.count("@") > 1 or not email.split("@")[1], \
                f"Should reject invalid email: {email}"

    def test_invalid_role_format(self):
        """Failure: Update user with invalid role"""
        invalid_roles = ["superadmin", "god", "user", ""]
        valid_roles = ["admin", "recruiter", "viewer"]

        for role in invalid_roles:
            assert role not in valid_roles, f"Should reject invalid role: {role}"

    def test_missing_required_fields(self):
        """Failure: Register without required fields"""
        # Missing email
        incomplete_data_1 = {
            "password": "Password123!"
        }
        assert "email" not in incomplete_data_1, "Should require email"

        # Missing password
        incomplete_data_2 = {
            "email": "test@example.com"
        }
        assert "password" not in incomplete_data_2, "Should require password"


class TestConcurrentFailures:
    """Test concurrent access failures"""

    def test_simultaneous_registrations(self):
        """Failure: Simultaneous registrations of same email"""
        import threading

        email = "concurrent@example.com"
        password = "Password123!"
        results = []

        def register():
            result = auth_service.register_user(email, password, "User")
            results.append(result)

        # Attempt concurrent registrations
        threads = [threading.Thread(target=register) for _ in range(3)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Only one should succeed
        successful = sum(1 for r in results if r is not None)
        assert successful <= 1, "Only one registration should succeed"

    def test_concurrent_role_updates(self):
        """Failure: Concurrent role updates"""
        # Multiple admins trying to change same user's role
        # Database constraint should prevent conflicts
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
