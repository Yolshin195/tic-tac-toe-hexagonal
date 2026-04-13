from pydantic import BaseModel
from app.enums import StatusGame
from app.entitys import GameEntity


class FilterSet(BaseModel):
    """
    Базовый класс для фильтров.
    Поля модели автоматически маппятся в WHERE условия.
    Для нестандартной логики — переопредели field_map.
    """

    def get_field_map(self) -> dict[str, callable]:
        """
        Маппинг поля фильтра -> функция которая возвращает SQLAlchemy условие.
        Переопредели в наследнике для кастомной логики.
        """
        return {}

    def apply(self, stmt, model):
        """Применяет все заданные поля фильтра к переданному statement."""
        field_map = self.get_field_map()

        for field_name, value in self.model_dump(exclude_none=True).items():
            if field_name in field_map:
                # Кастомная логика из field_map
                stmt = stmt.where(field_map[field_name](value))
            elif hasattr(model, field_name):
                # Автоматический eq для полей которые есть в модели
                stmt = stmt.where(getattr(model, field_name) == value)

        return stmt


class GameFilter(FilterSet):
    status: StatusGame | None = None

    def get_field_map(self) -> dict[str, callable]:
        return {
            "status": lambda v: GameEntity.status == v,
        }