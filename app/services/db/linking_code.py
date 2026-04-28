"""linking_code — CRUD-сервис для модели ``LinkingCode``."""

from app.models import LinkingCode
from app.services.db.base import BaseDBService


class LinkingCodeService(BaseDBService[LinkingCode]):
    """Сервис работы с одноразовыми кодами привязки канала к лендингу."""

    model = LinkingCode
