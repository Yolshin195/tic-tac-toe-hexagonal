from enum import Enum


class Simbol(str, Enum):
    X = "X"
    O = "O"


class StatusGame(str, Enum):
    ACTIVE = "Active"
    WIN_USER_ONE = "Win_user_one"
    WIN_USER_TWO = "Win_user_two"
    DRAW = "Draw"


class EventType(str, Enum):
    MESSAGE = "MESSAGE"
    ERROR = "ERROR"
    SYSTEM = "SYSTEM"


class ErrorCode(str, Enum):
    # Base
    INTERNAL_ERROR = "INTERNAL_ERROR"
    # Auth / Security
    ACCESS_DENIED = "ACCESS_DENIED"
    INVALID_CREDENTIALS = "INVALID_CREDENTIALS"
    # Entities
    NOT_FOUND = "NOT_FOUND"
    # Game
    GAME_ERROR = "GAME_ERROR"
    # DB
    DB_ERROR = "DB_ERROR"
