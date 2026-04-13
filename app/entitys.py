from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey, CheckConstraint, UniqueConstraint
from sqlalchemy import Enum as Enumsql

from app.enums import Simbol, StatusGame


class BaseEntity(DeclarativeBase):
    id: Mapped[int] = mapped_column(primary_key=True)


class UserEntity(BaseEntity):
    __tablename__ = "users"

    username: Mapped[str] = mapped_column(unique=True)
    hashed_password: Mapped[str] = mapped_column()


class GameEntity(BaseEntity):
    __tablename__ = "games"

    name: Mapped[str] = mapped_column()
    status: Mapped[StatusGame] = mapped_column(
        Enumsql(StatusGame, native_enum=False),
        default=StatusGame.ACTIVE,  # Значение на стороне Python
        server_default=StatusGame.ACTIVE.value,  # Значение на стороне БД (SQL)
        nullable=False,
    )

    user_one_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    user_two_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )
    user_one: Mapped[UserEntity] = relationship(foreign_keys=[user_one_id])
    user_two: Mapped[UserEntity | None] = relationship(
        foreign_keys=[user_two_id]
    )

    user_one_simbol: Mapped[Simbol] = mapped_column(
        Enumsql(Simbol, native_enum=False)
    )
    user_two_simbol: Mapped[Simbol] = mapped_column(
        Enumsql(Simbol, native_enum=False)
    )

    turns: Mapped[list["TurnEntity"]] = relationship(
        back_populates="game", cascade="all, delete-orphan"
    )


class TurnEntity(BaseEntity):
    __tablename__ = "turns"

    __table_args__ = (
        UniqueConstraint("game_id", "number", name="uq_game_turn_number"),
        CheckConstraint(
            "number >= 0 AND number <= 8", name="check_turn_range"
        ),
    )

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    user: Mapped[UserEntity] = relationship(foreign_keys=[user_id])

    game_id: Mapped[int] = mapped_column(ForeignKey("games.id"))
    game: Mapped["GameEntity"] = relationship(back_populates="turns")

    number: Mapped[int] = mapped_column()
    simbol: Mapped[Simbol] = mapped_column(Enumsql(Simbol, native_enum=False))


# class EventEntity(BaseEntity):
#     __tablename__ = "events"

#     user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
#     user: Mapped[UserEntity] = relationship(foreign_keys=[user_id])

#     game_id: Mapped[int] = mapped_column(ForeignKey("games.id"))
#     game: Mapped['GameEntity'] = relationship(back_populates="turns")

# type: Mapped[EventType] = mapped_column(Enumsql(EventType, native_enum=False))
#     message: Mapped[str | None] = mapped_column(nullable=True)
