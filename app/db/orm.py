import asyncio
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, AsyncGenerator, Dict, List, Optional

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Integer, String, Text, delete, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from app.config import DATABASE_URL

PROJECT_ROOT = Path(__file__).resolve().parents[2]

# DATABASE_URL comes from app/.env POSTGRES_* values, or sqlite if those are unset.

engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )


class Timeline(Base):
    __tablename__ = "timeline"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), index=True, nullable=True)
    title: Mapped[str] = mapped_column(String(255))
    category: Mapped[str] = mapped_column(String(128), default="")
    source: Mapped[str] = mapped_column(String(32), default="user")
    raw_data: Mapped[str] = mapped_column(Text)
    structured: Mapped[Dict[str, Any]] = mapped_column(JSON)
    timeline_plan: Mapped[Dict[str, Any]] = mapped_column(JSON)
    rewards: Mapped[Dict[str, Any]] = mapped_column(JSON)
    compiled: Mapped[Dict[str, Any]] = mapped_column(JSON)
    extracted_content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    difficulty_score: Mapped[int] = mapped_column(Integer, default=0)
    total_points: Mapped[int] = mapped_column(Integer, default=0)
    approved: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )


def run_migrations() -> None:
    from alembic import command
    from alembic.config import Config

    config = Config(str(PROJECT_ROOT / "alembic.ini"))
    command.upgrade(config, "head")


async def init_db() -> None:
    await asyncio.to_thread(run_migrations)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session


async def get_user_by_email(session: AsyncSession, email: str) -> Optional[User]:
    result = await session.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def get_user_by_id(session: AsyncSession, user_id: int) -> Optional[User]:
    result = await session.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def create_user(session: AsyncSession, email: str, hashed_password: str) -> User:
    user = User(email=email, hashed_password=hashed_password)
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


async def flush_users(session: AsyncSession) -> int:
    """Delete every row in the users table. Intended for local testing."""
    result = await session.execute(delete(User))
    await session.commit()
    return int(result.rowcount or 0)


async def create_timeline(
    session: AsyncSession,
    *,
    user_id: int,
    title: str,
    category: str,
    source: str,
    raw_data: str,
    structured: Dict[str, Any],
    timeline_plan: Dict[str, Any],
    rewards: Dict[str, Any],
    compiled: Dict[str, Any],
    total_points: int,
    approved: bool,
    extracted_content: str = "",
    difficulty_score: int = 0,
) -> Timeline:
    row = Timeline(
        user_id=user_id,
        title=title,
        category=category,
        source=source,
        raw_data=raw_data,
        structured=structured,
        timeline_plan=timeline_plan,
        rewards=rewards,
        compiled=compiled,
        extracted_content=extracted_content,
        difficulty_score=difficulty_score,
        total_points=total_points,
        approved=approved,
    )
    session.add(row)
    await session.commit()
    await session.refresh(row)
    return row


async def get_timeline(
    session: AsyncSession,
    timeline_id: int,
    user_id: int,
) -> Optional[Timeline]:
    result = await session.execute(
        select(Timeline).where(Timeline.id == timeline_id, Timeline.user_id == user_id)
    )
    return result.scalar_one_or_none()


async def list_timelines(session: AsyncSession, user_id: int) -> List[Timeline]:
    result = await session.execute(
        select(Timeline).where(Timeline.user_id == user_id).order_by(Timeline.id.desc())
    )
    return list(result.scalars().all())


async def main():

    async for session in get_db():
        user = await get_user_by_email(session, "test@example.com")
        print(user)
        print(user.email)
        print(user.hashed_password)
        

if __name__ == "__main__":
    asyncio.run(main())