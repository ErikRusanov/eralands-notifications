"""linking_code — CRUD-сервис для модели ``LinkingCode``."""

from sqlalchemy import select

from app.models import LinkingCode
from app.services.db.base import BaseDBService


class LinkingCodeService(BaseDBService[LinkingCode]):
    """Сервис работы с одноразовыми кодами привязки канала к лендингу."""

    model = LinkingCode

    async def get_by_code(self, code: str) -> LinkingCode | None:
        """Возвращает запись по уникальному значению ``code`` или ``None``.

        Не фильтрует по ``used_at``/``expires_at`` — раздельная обработка
        веток (нет / погашен / просрочен) лежит на доменном сервисе.

        Аргументы:
            code: Открытый одноразовый код, введённый пользователем.
        """
        stmt = select(LinkingCode).where(LinkingCode.code == code)
        return (await self.session.scalars(stmt)).one_or_none()
