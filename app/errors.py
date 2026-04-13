from http import HTTPStatus
from app.enums import ErrorCode


class AppError(Exception):
    """Базовая ошибка приложения"""

    error_code: ErrorCode = ErrorCode.INTERNAL_ERROR

    def __init__(
        self,
        message: str,
        status_code: int = HTTPStatus.INTERNAL_SERVER_ERROR,
        details: dict | None = None,
    ):
        self.message = message
        self.status_code = status_code
        self.details = details or {}

    def to_dict(self):
        return {
            "error": self.__class__.__name__,
            "message": self.message,
            "details": self.details,
        }


class ServiceError(AppError):
    """Ошибка бизнес-логики"""

    pass


class GameServiceError(ServiceError):
    error_code = ErrorCode.GAME_ERROR

    def __init__(self, message: str = "Database error"):
        super().__init__(
            message,
            status_code=HTTPStatus.BAD_REQUEST,
        )


class RepositoryError(AppError):
    """Ошибка базы данных"""

    error_code = ErrorCode.DB_ERROR

    def __init__(self, message: str = "Database error"):
        super().__init__(
            message,
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
        )


class EntityNotFoundError(ServiceError):
    """Объект не найден"""

    error_code = ErrorCode.NOT_FOUND

    def __init__(self, entity: str, entity_id: str | int):
        super().__init__(
            message=f"{entity} not found",
            status_code=HTTPStatus.NOT_FOUND,
            details={"id": entity_id},
        )


class SecurityError(ServiceError):
    """Ошибка безопасности"""

    error_code = ErrorCode.ACCESS_DENIED

    def __init__(self, message: str = "Access denied"):
        super().__init__(
            message,
            status_code=HTTPStatus.FORBIDDEN,
        )
