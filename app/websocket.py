from typing import Dict, List
from fastapi.websockets import WebSocket


class ConnectionManager:
    def __init__(self):
        # Словарь: { game_id: [список_вебсокетов] }
        self.active_connections: Dict[int, List[WebSocket]] = {}

    async def connect(self, game_id: int, websocket: WebSocket):
        await websocket.accept()
        if game_id not in self.active_connections:
            self.active_connections[game_id] = []
        self.active_connections[game_id].append(websocket)

    def disconnect(self, game_id: int, websocket: WebSocket):
        if game_id in self.active_connections:
            self.active_connections[game_id].remove(websocket)
            if not self.active_connections[game_id]:
                del self.active_connections[game_id]

    async def broadcast_update(self, game_id: int, message: str):
        """Отправляет сигнал 'update' всем игрокам в комнате game_id"""
        if game_id in self.active_connections:
            for connection in self.active_connections[game_id]:
                try:
                    # Можно отправить просто текст "refresh",
                    # чтобы фронтенд понял: пора вызвать GET /api/game/id
                    await connection.send_text(message)
                except Exception:
                    # Если соединение битое, менеджер очистит его позже или при дисконнекте
                    pass


manager = ConnectionManager()

__all__ = ["manager"]
