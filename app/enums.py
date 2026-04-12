from enum import Enum

class Simbol(str, Enum):
    X = "X"
    O = "O"


class StatusGame(str, Enum):
    ACTIVE = "Active"
    WIN_USER_ONE = "Win_user_one"
    WIN_USER_TWO = "Win_user_two"
    DRAW = "Draw"