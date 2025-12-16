from typing import List, Optional

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from models.user import User


class UserRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, username: str, email: str, password_hash: str) -> User:
        user = User(username=username, email=email, password_hash=password_hash)
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def get_by_id(self, user_id: int) -> Optional[User]:
        stmt = select(User).where(User.id == user_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> Optional[User]:
        stmt = select(User).where(User.email == email)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_username(self, username: str) -> Optional[User]:
        stmt = select(User).where(User.username == username)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all(self, skip: int = 0, limit: int = 100) -> List[User]:
        stmt = select(User).offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def update_user(
        self,
        user_id: int,
        username: Optional[str] = None,
        email: Optional[str] = None,
        password_hash: Optional[str] = None,
    ) -> Optional[User]:
        update_data = {}

        if username is not None:
            update_data["username"] = username

        if email is not None:
            update_data["email"] = email

        if password_hash is not None:
            update_data["password_hash"] = password_hash

        if not update_data:
            return await self.get_by_id(user_id)

        stmt = update(User).where(User.id == user_id).values(**update_data)
        await self.db.execute(stmt)
        await self.db.commit()

        return await self.get_by_id(user_id)

    async def delete_user(self, user_id: int) -> bool:
        user = await self.get_by_id(user_id)
        if not user:
            return False

        stmt = delete(User).where(User.id == user_id)
        await self.db.execute(stmt)
        await self.db.commit()
        return True

    async def exists_by_email(self, email: str) -> bool:
        user = await self.get_by_email(email)
        return user is not None

    async def exists_by_username(self, username: str) -> bool:
        user = await self.get_by_username(username)
        return user is not None
