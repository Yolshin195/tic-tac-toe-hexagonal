from pydantic import BaseModel, Field, computed_field
from app.enums import Simbol, StatusGame


class TokenPayload(BaseModel):
    """Структура данных внутри токена."""
    sub: str  # Обычно ID пользователя (subject)
    username: str
    role: str = "user"
    # Поля 'exp' и 'iat' добавятся библиотекой jwt автоматически, 
    # но их можно описать здесь для типизации.

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class GetUserRequest(BaseModel):
    username: str


class RegisterUserRequest(BaseModel):
    username: str
    password: str


class LoggingUserRequest(BaseModel):
    username: str
    password: str


class JoinGameRequest(BaseModel):
    game_id: int


class MakeTurnRequest(BaseModel):
    number: int = Field(..., ge=0, le=8)


class User(BaseModel):
    id: int
    username: str


class Turn(BaseModel):
    id: int
    game_id: int
    user: User
    simbol: Simbol
    number: int = Field(..., ge=0, le=8)


class CreateGameRequest(BaseModel):
    name: str


class Game(BaseModel):
    id: int
    name: str
    status: StatusGame
    user_one: User | None
    user_two: User | None
    user_one_simbol: Simbol
    user_two_simbol: Simbol
    turns: list[Turn] = Field(default_factory=list)

    @computed_field
    @property
    def current_user(self) -> User | None:
        if self.turns:
            last_turn = max(self.turns, key=lambda turn: turn.id)
            if self.user_one.id == last_turn.user.id:
                return self.user_two
            if self.user_two.id == last_turn.user.id:
                return self.user_one
        return None
        

if __name__ == "__main__":
    # Создаем пользователей
    user_1 = User(id=1, name="Aleksey")
    user_2 = User(id=2, name="Pinpan")

    # Инициализируем объект Game
    game_example = Game(
        id=101,
        name="Pinpan vs Aleksey",
        user_one=user_1,
        user_two=user_2,
        user_one_simbol=Simbol.X,
        user_two_simbol=Simbol.O,
        turns=[
            Turn(id=1, user=user_1, simbol=Simbol.X, number=4),
            Turn(id=2, user=user_2, simbol=Simbol.O, number=0),
            Turn(id=3, user=user_1, simbol=Simbol.X, number=8),
            Turn(id=4, user=user_2, simbol=Simbol.O, number=2),
            Turn(id=5, user=user_1, simbol=Simbol.X, number=1),
            Turn(id=6, user=user_2, simbol=Simbol.O, number=7),
            Turn(id=7, user=user_1, simbol=Simbol.X, number=3),
            Turn(id=8, user=user_2, simbol=Simbol.O, number=5),
            Turn(id=9, user=user_1, simbol=Simbol.X, number=6),
        ]
    )

    # Вывод для проверки
    print(game_example.model_dump_json(indent=4))