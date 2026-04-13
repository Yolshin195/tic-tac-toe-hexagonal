from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from sqlalchemy.orm import joinedload, selectinload

from app.entitys import UserEntity, GameEntity, TurnEntity
from app.models import User
from app.enums import StatusGame
from app.filters import GameFilter


class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_username(self, username: str) -> UserEntity | None:
        stmt = select(UserEntity).where(UserEntity.username == username)
        user = (await self.session.execute(stmt)).scalar_one_or_none()
        return user

    async def get_by_id(self, user_id: int) -> UserEntity | None:
        stmt = select(UserEntity).where(UserEntity.id == user_id)
        user = (await self.session.execute(stmt)).scalar_one_or_none()
        return user

    async def create_user(self, username: str, hashed_password: str) -> UserEntity:
        user = UserEntity(username=username, hashed_password=hashed_password)
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user


class GameRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list(
        self, user_id: int, filters: GameFilter | None = None
    ) -> list[GameEntity]:
        stmt = (
            select(GameEntity)
            .where(
                or_(
                    GameEntity.user_one_id == user_id,
                    GameEntity.user_two_id == user_id,
                )
            )
            .options(
                joinedload(GameEntity.user_one),
                joinedload(GameEntity.user_two),
                selectinload(GameEntity.turns),
            )
        )

        if filters:
            stmt = filters.apply(stmt, GameEntity)

        return (await self.session.execute(stmt)).scalars()

    async def get_active_by_user_id(self, user_id: int) -> GameEntity | None:
        stmt = (
            select(GameEntity)
            .where(
                or_(
                    GameEntity.user_one_id == user_id,
                    GameEntity.user_two_id == user_id,
                ),
                GameEntity.status == StatusGame.ACTIVE,
            )
            .options(
                joinedload(GameEntity.user_one),
                joinedload(GameEntity.user_two),
                selectinload(GameEntity.turns),
            )
        )
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def get_by_id_and_user_id(
        self, game_id: int, user_id: int
    ) -> GameEntity | None:
        stmt = (
            select(GameEntity)
            .where(
                or_(
                    GameEntity.user_one_id == user_id,
                    GameEntity.user_two_id == user_id,
                ),
                GameEntity.id == game_id,
            )
            .options(
                joinedload(GameEntity.user_one),
                joinedload(GameEntity.user_two),
                selectinload(GameEntity.turns),
            )
        )
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def get_game_for_join(self, game_id: int) -> GameEntity | None:
        stmt = (
            select(GameEntity)
            .where(
                GameEntity.id == game_id,
                GameEntity.status == StatusGame.ACTIVE,
                GameEntity.user_two_id.is_(None),
            )
            .with_for_update()
            .options(
                joinedload(GameEntity.user_one),
                joinedload(GameEntity.user_two),
                selectinload(GameEntity.turns),
            )
        )
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def get_game_for_turn(self, user_id: int) -> GameEntity | None:
        stmt = (
            select(GameEntity)
            .where(
                or_(
                    GameEntity.user_one_id == user_id,
                    GameEntity.user_two_id == user_id,
                ),
                GameEntity.status == StatusGame.ACTIVE,
            )
            .options(selectinload(GameEntity.turns))
        )
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def save(self, game: GameEntity) -> GameEntity:
        self.session.add(game)
        await self.session.commit()
        await self.session.refresh(game)
        return game


class TurnRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def save(self, turn: TurnEntity) -> TurnEntity:
        self.session.add(turn)
        await self.session.commit()
        await self.session.refresh(turn)
        await self.session.flush()
        return turn
