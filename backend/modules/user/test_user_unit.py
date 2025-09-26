"""Unit tests for the user service."""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import Mock

import pytest

from modules.user.models import UserModel
from modules.user.repo import UserRepo
from modules.user.service import AuthenticationResult, UserLogin, UserRegister, UserService, UserUpdate


class TestUserService:
    """Behavioral tests for the UserService layer."""

    def _build_user(self, **overrides: object) -> UserModel:
        defaults: dict[str, object] = {
            "id": 1,
            "email": "user@example.com",
            "password_hash": "pbkdf2_sha256$0$00$00",
            "name": "Test User",
            "role": "learner",
            "is_active": True,
            "created_at": datetime.now(UTC),
            "updated_at": datetime.now(UTC),
        }
        defaults.update(overrides)
        return UserModel(**defaults)

    def test_register_creates_user_with_hashed_password(self) -> None:
        repo = Mock(spec=UserRepo)
        repo.by_email.return_value = None

        service = UserService(repo)

        def _create(**kwargs: object) -> UserModel:
            return self._build_user(id=1, password_hash=kwargs["password_hash"], email=kwargs["email"], name=kwargs["name"])

        repo.create.side_effect = _create

        payload = UserRegister(email="user@example.com", password="password123", name="Test User")
        result = service.register(payload)

        repo.by_email.assert_called_once_with("user@example.com")
        assert repo.create.call_count == 1
        hashed_password = repo.create.call_args.kwargs["password_hash"]
        assert isinstance(hashed_password, str)
        assert hashed_password.startswith("pbkdf2_sha256$")
        assert result.email == payload.email
        assert result.name == payload.name

    def test_register_raises_when_email_exists(self) -> None:
        repo = Mock(spec=UserRepo)
        repo.by_email.return_value = self._build_user()
        service = UserService(repo)

        with pytest.raises(ValueError):
            service.register(UserRegister(email="user@example.com", password="password123", name="User"))

    def test_authenticate_returns_user_on_success(self) -> None:
        repo = Mock(spec=UserRepo)
        service = UserService(repo)

        hashed_password = service._hash_password("password123")
        user = self._build_user(password_hash=hashed_password)
        repo.by_email.return_value = user

        result = service.authenticate(UserLogin(email="user@example.com", password="password123"))

        assert isinstance(result, AuthenticationResult)
        assert result.user.email == "user@example.com"

    def test_authenticate_raises_for_invalid_password(self) -> None:
        repo = Mock(spec=UserRepo)
        service = UserService(repo)

        hashed_password = service._hash_password("password123")
        user = self._build_user(password_hash=hashed_password)
        repo.by_email.return_value = user

        with pytest.raises(ValueError):
            service.authenticate(UserLogin(email="user@example.com", password="wrong"))

    def test_get_profile_returns_none_when_missing(self) -> None:
        repo = Mock(spec=UserRepo)
        repo.by_id.return_value = None
        service = UserService(repo)

        assert service.get_profile(123) is None

    def test_update_profile_updates_name_and_password(self) -> None:
        repo = Mock(spec=UserRepo)
        service = UserService(repo)

        original_hash = service._hash_password("password123")
        user = self._build_user(password_hash=original_hash)
        repo.by_id.return_value = user
        repo.save.return_value = user

        payload = UserUpdate(name="New Name", password="newpassword123")
        result = service.update_profile(1, payload)

        repo.by_id.assert_called_once_with(1)
        repo.save.assert_called_once_with(user)
        assert result.name == "New Name"
        assert user.password_hash != original_hash
