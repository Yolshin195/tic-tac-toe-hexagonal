import fastapi
from fastapi import Depends, Request
from fastapi.websockets import WebSocket
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm
from app.dependencies import get_user_service
from app.dependencies import get_current_user
from app.dependencies import get_game_service
from app.services import UserService, GameService
from app.errors import AppError
from app.models import (
    LoggingUserRequest,
    RegisterUserRequest,
    CreateGameRequest,
    JoinGameRequest,
    TokenResponse,
    MakeTurnRequest,
    User,
    Game,
)
from app.websocket import manager as ws_manager

app = fastapi.FastAPI()

@app.exception_handler(AppError)
async def app_error_handler(
    request: Request,
    exc: AppError,
):
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.to_dict(),
    )

@app.get("/", response_class=HTMLResponse)
async def main():
    return FileResponse('templates/index.html')

@app.post("/api/register")
async def register(
    data: RegisterUserRequest,
    service: UserService = Depends(get_user_service)
) -> TokenResponse:
    return await service.register(data)

@app.post("/api/login/form")
async def login_form(
    form_data: OAuth2PasswordRequestForm = Depends(),
    service: UserService = Depends(get_user_service)
) -> TokenResponse:
    data = LoggingUserRequest(
        username=form_data.username,
        password=form_data.password
    )
    return await service.loggin(data)


@app.get("/api/me")
async def get_current_user(user: User = Depends(get_current_user)) -> User:
    return user


@app.post("/api/game")
async def create_game(
    data: CreateGameRequest,
    service: GameService = Depends(get_game_service)
) -> Game:
    return await service.start_game(data)


@app.get("/api/game")
async def get_active_game(
    service: GameService = Depends(get_game_service)
) -> Game:
    return await service.get_active_game()


@app.get("/api/game/{game_id}")
async def get_active_game(
    game_id: int,
    service: GameService = Depends(get_game_service)
) -> Game:
    return await service.get_game(game_id)


@app.post("/api/game/join")
async def join(
    data: JoinGameRequest,
    service: GameService = Depends(get_game_service)
) -> Game:
    game = await service.join_game(data)
    await ws_manager.broadcast_update(game.id)
    return game


@app.post("/api/game/turn")
async def turn(
    data: MakeTurnRequest,
    service: GameService = Depends(get_game_service)
) -> None:
    turn = await service.make_turn(data)
    await ws_manager.broadcast_update(turn.game_id)
    return turn


@app.post("/api/game/message")
async def send_message(
        service: GameService = Depends(get_game_service)
    ) -> None:
    game = await service.get_active_game()
    await ws_manager.broadcast_update(game.id)


@app.websocket("/ws/{game_id}")
async def websocket_endpoint(websocket: WebSocket, game_id: int):
    await ws_manager.connect(game_id, websocket)
    try:
        while True:
            # Просто держим соединение открытым
            await websocket.receive_text()
    except Exception:
        # Обработка разрыва соединения (закрытие вкладки и т.д.)
        ws_manager.disconnect(game_id, websocket)