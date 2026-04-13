import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any

from app.models import TokenPayload, TokenResponse


class SecurityService:
    def __init__(self, secret_key: str, algorithm: str = "HS256"):
        self.secret_key = secret_key
        self.algorithm = algorithm
        # Инициализируем hasher с параметрами по умолчанию (рекомендовано OWASP)
        self._ph = PasswordHasher()

    # --- Работа с паролями (используем argon2-cffi) ---

    def hash_password(self, password: str) -> str:
        """
        Создает хеш пароля с использованием Argon2id.
        Библиотека автоматически генерирует соль и добавляет параметры сложности в строку.
        """
        return self._ph.hash(password)

    def verify_password(
        self, plain_password: str, hashed_password: str
    ) -> bool:
        """
        Проверяет пароль.
        Argon2 хранит параметры алгоритма в самой строке хеша.
        """
        try:
            return self._ph.verify(hashed_password, plain_password)
        except VerifyMismatchError:
            return False

    def check_needs_rehash(self, hashed_password: str) -> bool:
        """
        Проверяет, нужно ли обновить хеш (например, если вы изменили настройки сложности).
        Полезно для плавного обновления безопасности без сброса паролей.
        """
        return self._ph.check_needs_rehash(hashed_password)

    # --- Работа с JWT ---

    def create_token(
        self, payload: TokenPayload, expires_minutes: int = 30
    ) -> TokenResponse:
        """Принимает модель Pydantic и возвращает модель TokenResponse."""
        # Превращаем модель в словарь для PyJWT
        data_to_encode = payload.model_dump()

        expire = datetime.now(timezone.utc) + timedelta(
            minutes=expires_minutes
        )
        data_to_encode.update({"exp": expire})

        encoded_jwt = jwt.encode(
            data_to_encode, self.secret_key, algorithm=self.algorithm
        )

        return TokenResponse(access_token=encoded_jwt)

    def decode_token(self, token: str) -> Optional[TokenPayload]:
        """Расшифровывает токен и возвращает валидированную модель Pydantic."""
        try:
            payload_dict = jwt.decode(
                token, self.secret_key, algorithms=[self.algorithm]
            )
            # Валидируем словарь через Pydantic и возвращаем объект
            return TokenPayload(**payload_dict)
        except (jwt.ExpiredSignatureError, jwt.InvalidTokenError, Exception):
            # Exception здесь поймает и ошибки валидации Pydantic, если в токене не те поля
            return None


# --- Тестирование ---
if __name__ == "__main__":
    service = SecurityService(secret_key="MY_VERY_SECRET_KEY")

    # Проверка пароля
    my_pass = "admin123"
    hashed = service.hash_password(my_pass)
    # Хеш Argon2 будет выглядеть примерно так: $argon2id$v=19$m=65536,t=3,p=4$...
    print(f"Хеш Argon2 в БД: {hashed}")

    is_valid = service.verify_password("admin123", hashed)
    print(f"Пароль верный? {is_valid}")

    # Проверка на необходимость рехеширования (если настройки поменяются в будущем)
    print(f"Нужен рехеш? {service.check_needs_rehash(hashed)}")

    # 1. Создаем данные пользователя
    user_payload = TokenPayload(sub="123", username="john_doe", role="admin")

    # 2. Генерируем токен (на выходе модель TokenResponse)
    token_data = service.create_token(user_payload)
    print(f"Token for client: {token_data.access_token}")

    # 3. Расшифровываем (на выходе модель TokenPayload)
    decoded_user = service.decode_token(token_data.access_token)

    if decoded_user:
        print(f"User ID: {decoded_user.sub}")
        print(f"Username: {decoded_user.username}")
