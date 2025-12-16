from typing import List, Optional

from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession

from models.user import User, UserResponse
from repositories.user import UserRepository


class UserService:
    def __init__(self, db: AsyncSession):
        self.repository = UserRepository(db)
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    def _hash_password(self, password: str) -> str:
        return self.pwd_context.hash(password)

    def _verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return self.pwd_context.verify(plain_password, hashed_password)

    async def create_user(
        self, username: str, email: str, password: str
    ) -> UserResponse:

        if await self.repository.exists_by_email(email):
            raise ValueError(f"Email '{email}' is already registered")

        if await self.repository.exists_by_username(username):
            raise ValueError(f"Username '{username}' is already taken")

        password_hash = self._hash_password(password)
        user = await self.repository.create(
            username=username, email=email, password_hash=password_hash
        )

        return self._to_user_response(user)

    async def get_user_by_id(self, user_id: int) -> Optional[UserResponse]:
        user = await self.repository.get_by_id(user_id)
        return self._to_user_response(user) if user else None

    async def get_user_by_email(self, email: str) -> Optional[UserResponse]:
        user = await self.repository.get_by_email(email)
        return self._to_user_response(user) if user else None

    async def get_user_by_username(self, username: str) -> Optional[UserResponse]:
        user = await self.repository.get_by_username(username)
        return self._to_user_response(user) if user else None

    async def get_all_users(
        self, skip: int = 0, limit: int = 100
    ) -> List[UserResponse]:

        users = await self.repository.get_all(skip=skip, limit=limit)
        return [self._to_user_response(user) for user in users]

    async def update_user(
        self,
        user_id: int,
        username: Optional[str] = None,
        email: Optional[str] = None,
        password: Optional[str] = None,
    ) -> Optional[UserResponse]:

        existing_user = await self.repository.get_by_id(user_id)
        if not existing_user:
            return None

        if email and email != existing_user.email:
            email_user = await self.repository.get_by_email(email)
            if email_user and email_user.id != user_id:
                raise ValueError(f"Email '{email}' is already registered")

        if username and username != existing_user.username:
            username_user = await self.repository.get_by_username(username)
            if username_user and username_user.id != user_id:
                raise ValueError(f"Username '{username}' is already taken")

        password_hash = self._hash_password(password) if password else None

        updated_user = await self.repository.update_user(
            user_id=user_id,
            username=username,
            email=email,
            password_hash=password_hash,
        )

        return self._to_user_response(updated_user) if updated_user else None

    async def delete_user(self, user_id: int) -> bool:
        return await self.repository.delete_user(user_id)

    async def authenticate_user(
        self, email: str, password: str
    ) -> Optional[UserResponse]:
        user = await self.repository.get_by_email(email)
        if not user:
            return None

        if not self._verify_password(password, user.password_hash):
            return None

        return self._to_user_response(user)

    def _to_user_response(self, user: User) -> UserResponse:
        return UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            created_at=user.created_at,
            updated_at=user.updated_at,
        )
