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
    SendMessageRequest,
    CreateGameRequest,
    JoinGameRequest,
    TokenResponse,
    MakeTurnRequest,
    User,
    Game,
    Turn,
    ResponseWrapper,
    ErrorWrapper,
)
from app.filters import GameFilter
from app.websocket import manager as ws_manager

app = fastapi.FastAPI()


@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError):
    wrapper = ResponseWrapper().make_error(
        ErrorWrapper(
            code=exc.error_code,
            message=exc.message,
            params=exc.details or None,
        )
    )
    return JSONResponse(
        status_code=exc.status_code, content=wrapper.model_dump()
    )


@app.get("/", response_class=HTMLResponse)
async def main():
    return FileResponse("templates/index.html")


@app.post("/api/register", response_model=ResponseWrapper[TokenResponse])
async def register(
    data: RegisterUserRequest, service: UserService = Depends(get_user_service)
) -> ResponseWrapper[TokenResponse]:
    result = await service.register(data)
    return ResponseWrapper[TokenResponse].make_success(result)


@app.post("/api/login/form", response_model=TokenResponse)
async def login_form(
    form_data: OAuth2PasswordRequestForm = Depends(),
    service: UserService = Depends(get_user_service),
) -> ResponseWrapper[TokenResponse]:
    data = LoggingUserRequest(
        username=form_data.username, password=form_data.password
    )
    result = await service.loggin(data)
    return result


@app.get("/api/me", response_model=ResponseWrapper[User])
async def get_current_user(
    user: User = Depends(get_current_user),
) -> ResponseWrapper[User]:
    return ResponseWrapper[User].make_success(user)


@app.get(
    path="/api/game/my",
    response_model=ResponseWrapper[list[Game]],
)
async def get_my_game(
    filters: GameFilter = Depends(),
    service: GameService = Depends(get_game_service),
) -> ResponseWrapper[list[Game]]:
    rows = await service.get_all_my_game(filters=filters)
    return ResponseWrapper[list[Game]].make_success(rows)


@app.post("/api/game", response_model=ResponseWrapper[Game])
async def create_game(
    data: CreateGameRequest,
    service: GameService = Depends(get_game_service),
) -> ResponseWrapper[Game]:
    game = await service.start_game(data)
    return ResponseWrapper[Game].make_success(game)


@app.get("/api/game", response_model=ResponseWrapper[Game])
async def get_active_game(
    service: GameService = Depends(get_game_service),
) -> ResponseWrapper[Game]:
    game = await service.get_active_game()
    return ResponseWrapper[Game].make_success(game)


@app.get("/api/game/{game_id}", response_model=ResponseWrapper[Game])
async def get_game_by_id(
    game_id: int, service: GameService = Depends(get_game_service)
) -> ResponseWrapper[Game]:
    game = await service.get_game(game_id)
    return ResponseWrapper[Game].make_success(game)


@app.post("/api/game/join", response_model=ResponseWrapper[Game])
async def join(
    data: JoinGameRequest, service: GameService = Depends(get_game_service)
) -> ResponseWrapper[Game]:
    game = await service.join_game(data)
    await ws_manager.broadcast_update(
        game.id,
        f"Присоединился игрок {game.user_two_simbol.value}: {game.user_two.username}",
    )
    return ResponseWrapper[Game].make_success(game)


@app.post("/api/game/turn", response_model=ResponseWrapper[Turn])
async def turn(
    data: MakeTurnRequest, service: GameService = Depends(get_game_service)
) -> ResponseWrapper[Turn]:
    turn_result: Turn = await service.make_turn(data)
    await ws_manager.broadcast_update(
        turn_result.game_id,
        f"Походил игрок {turn_result.simbol.value}: {turn_result.number}",
    )
    return ResponseWrapper[Turn].make_success(turn_result)


@app.post("/api/game/message", response_model=ResponseWrapper[bool])
async def send_message(
    data: SendMessageRequest, service: GameService = Depends(get_game_service)
) -> ResponseWrapper[bool]:
    game = await service.get_active_game()
    await ws_manager.broadcast_update(
        game.id, f"{service.user.username}: {data.message}"
    )
    return ResponseWrapper[bool].make_success(True)


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
