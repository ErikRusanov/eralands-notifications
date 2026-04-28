"""client — клиент Era Lands, владелец лендингов и каналов уведомлений."""

from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class Client(BaseModel):
    """Клиент Era Lands.

    Атрибуты:
        name: Произвольное имя клиента, которое мы видим в админке.
    """

    __tablename__ = "clients"

    name: Mapped[str] = mapped_column(nullable=False)
