from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from app.db import get_db_session
from app.repositories import UserRepository
from app.repositories import GameRepository
from app.repositories import TurnRepository
from app.services import UserService
from app.services import GameService
from app.security import SecurityService
from app.models import User
from app.config import SECRET_KEY


__all__ = [
    "get_user_service"
]


def get_security_service() -> SecurityService:
    return SecurityService(secret_key=SECRET_KEY)

def get_user_repository(session: AsyncSession = Depends(get_db_session)) -> UserRepository:
    return UserRepository(session)

def get_user_service(
    repo: UserRepository = Depends(get_user_repository),
    security_service: SecurityService = Depends(get_security_service)
) -> UserService:
    return UserService(repo=repo, security_service=security_service)


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/login/form")

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    service: UserService = Depends(get_user_service)
) -> User:
    """
    Middleware-подобная функция для проверки JWT.
    """
    user = await service.get_user_by_token(token)
    return user


async def get_game_repository(session: AsyncSession = Depends(get_db_session)) -> GameRepository:
    return GameRepository(session)


async def get_turn_repository(session: AsyncSession = Depends(get_db_session)) -> TurnRepository:
    return TurnRepository(session)


async def get_game_service(
    repo: GameRepository = Depends(get_game_repository),
    turn_repo: TurnRepository = Depends(get_turn_repository),
    user: User = Depends(get_current_user),
) -> GameService:
    return GameService(
        user=user,
        repo=repo,
        turn_repo=turn_repo,
    )