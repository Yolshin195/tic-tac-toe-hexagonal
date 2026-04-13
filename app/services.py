from app.repositories import UserRepository, GameRepository, TurnRepository
from app.models import User, RegisterUserRequest, LoggingUserRequest
from app.security import SecurityService
from app.errors import SecurityError, GameServiceError
from app.models import TokenResponse, TokenPayload, Game, CreateGameRequest, Turn, MakeTurnRequest, JoinGameRequest
from app.entitys import GameEntity, TurnEntity
from app.enums import Simbol, StatusGame
from app.filters import GameFilter
import random
import logging


log = logging.getLogger(__name__)


class UserService:
    def __init__(self, repo: UserRepository, security_service: SecurityService):
        self.repo = repo
        self.security_service = security_service

    async def get_user_by_token(self, token: str) -> User:
        payload = self.security_service.decode_token(token)
        if payload is None:
            raise SecurityError("Токен не валидный")
        
        user = await self.repo.get_by_id(payload.sub)
        if user is None:
            raise SecurityError("Пользователь с таким id не найден")
        return User.model_validate(user, from_attributes=True)


    async def register(self, data: RegisterUserRequest) -> TokenResponse:
        user = await self.repo.get_by_username(data.username)
        if user is not None:
            raise SecurityError("Пользователь стаким именем не может быть зарегистрированн")
        
        hashed_password = self.security_service.hash_password(data.password)
        user = await self.repo.create_user(data.username, hashed_password)
        payload = TokenPayload(
            sub=str(user.id),
            username=user.username
        )
        token = self.security_service.create_token(payload)
        return token
    
    async def loggin(self, data: LoggingUserRequest) -> TokenResponse:
        user = await self.repo.get_by_username(data.username)
        if user is None:
            raise SecurityError("Пользователь не найден")
        if not self.security_service.verify_password(data.password, user.hashed_password):
            raise SecurityError("Не верный пароль")
        
        payload = TokenPayload(
            sub=str(user.id),
            username=user.username
        )
        token = self.security_service.create_token(payload)
        return token
        

class GameService:
    def __init__(self, user: User, repo: GameRepository, turn_repo: TurnRepository):
        self.user = user
        self.repo = repo
        self.turn_repo = turn_repo
    
    async def start_game(self, data: CreateGameRequest) -> Game:
        active_game = await self.repo.get_active_by_user_id(self.user.id)
        if active_game is not None:
            raise GameServiceError(f"У вас уже запущена одна активная игра, сначала завершите её Game name: {active_game.name}")

        symbols = list(Simbol)
        random.shuffle(symbols)

        game = GameEntity(
            name=data.name,
            status=StatusGame.ACTIVE,
            user_one_id=self.user.id,
            user_two_id=None,
            user_one_simbol=symbols[0],
            user_two_simbol=symbols[1],
            turns = []
        )

        game = await self.repo.save(game)

        active_game = await self.repo.get_active_by_user_id(self.user.id)
        if active_game is None:
            raise GameServiceError(f"Не смогли запросить игру повторно, обновите страницу")

        return Game.model_validate(active_game, from_attributes=True)

    async def join_game(self, data: JoinGameRequest) -> Game:
        active_game = await self.repo.get_game_for_join(data.game_id)
        if active_game is None:
            raise GameServiceError(f"Вы не можете присоединится к этой игре")
        
        active_game.user_two_id = self.user.id
        await self.repo.save(active_game)
        return Game.model_validate(active_game, from_attributes=True)
        

    async def make_turn(self, data: MakeTurnRequest) -> Turn:
        active_game = await self.repo.get_game_for_turn(self.user.id)
        if active_game is None:
            raise GameServiceError(f"Вы не можете выполнить ход в этой игре")
        
        if active_game.turns:
            last_turn = max(active_game.turns, key=lambda turn: turn.id)
            if last_turn.user_id == self.user.id:
                raise GameServiceError(f"Сейчас не ваш ход, дождитесь своего хода")
        
        if active_game.user_one_id == self.user.id:
            simbol = active_game.user_one_simbol
        elif active_game.user_two_id == self.user.id:
            simbol = active_game.user_two_simbol
        else:
            raise GameServiceError(f"Не удалось получиь символ для пользователя")

        turn = TurnEntity(
            user_id=self.user.id,
            game_id=active_game.id,
            number=data.number,
            simbol=simbol
        )
        turn = await self.turn_repo.save(turn)

        # Проверяем статус и обновляем его если нужно
        active_game.turns.append(turn)
        await self._update_status(active_game)

        return turn
    
    async def get_all_my_game(self, filters: GameFilter | None = None) -> list[Game]:
        rows = await self.repo.list(self.user.id, filters=filters)
        return [Game.model_validate(game, from_attributes=True) for game in rows]

    async def get_active_game(self) -> Game:
        active_game = await self.repo.get_active_by_user_id(self.user.id)
        if active_game is None:
            raise GameServiceError(f"У вас нету ни одной активной игры, создайте или присоединитесь к существующей")
        
        await self._update_status(active_game)

        return Game.model_validate(active_game, from_attributes=True)
    
    async def get_game(self, game_id: int) -> Game:
        active_game = await self.repo.get_by_id_and_user_id(game_id, self.user.id)
        if active_game is None:
            raise GameServiceError(f"У вас нету доступа к этой игре, создайте или присоединитесь к существующей")
        
        await self._update_status(active_game)

        return Game.model_validate(active_game, from_attributes=True)
    
    async def _update_status(self, active_game: GameEntity) -> None:
        new_status = await self._get_current_status(active_game)
        if active_game.status != new_status:
            active_game.status = new_status
            await self.repo.save(active_game)
    
    async def _get_current_status(self, game: GameEntity) -> StatusGame:
        """
        Логика проверки победителя
        """
        board = [None] * 9
        for turn in game.turns:
            board[turn.number] = turn.simbol
        
        winning = [
            (0, 1, 2),
            (3, 4, 5),
            (6, 7, 8),

            (0, 3, 6),
            (1, 4, 7),
            (2, 5, 8),

            (0, 4, 8),
            (2, 4, 6),
        ]

        for c1, c2, c3 in winning:
            if board[c1] is not None and board[c1] == board[c2] and board[c2] == board[c3]:
                if board[c1] == game.user_one_simbol:
                    return StatusGame.WIN_USER_ONE
                elif board[c1] == game.user_two_simbol:
                    return StatusGame.WIN_USER_TWO
                else:
                    raise GameServiceError(
                        f"Обнаружена выигрышная комбинация ({c1}, {c2}, {c3}) с символом '{board[c1]}', "
                        f"однако данный символ не закреплен ни за одним из участников игры."
                    )

        if len(game.turns) == 9:
            return StatusGame.DRAW
        
        return StatusGame.ACTIVE
        

        
        
