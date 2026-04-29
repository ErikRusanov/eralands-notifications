"""errors — доменные исключения, которые маппятся в HTTP-ответы.

Иерархия специально плоская: класс ошибки определяет HTTP-код, текст
исключения попадает в поле ``detail`` стандартного ``ErrorResponse``.
Маппинг ``класс → код`` живёт в ``app.core.errors``.
"""


class DomainError(Exception):
    """Базовое доменное исключение. Само по себе не возникает."""


class NotFoundError(DomainError):
    """Сущность не найдена. Маппится в HTTP 404."""


class ConflictError(DomainError):
    """Бизнес-конфликт: дубль, неверное состояние, повторное действие. HTTP 409."""


class AuthError(DomainError):
    """Ошибка аутентификации или авторизации. Маппится в HTTP 401."""


class LinkingCodeNotFoundError(NotFoundError):
    """Кода нет в БД либо он уже погашен.

    Обе ситуации сливаются в одну ветку намеренно: чтобы не подтверждать
    клиенту, что введённый код когда-либо существовал.
    """


class LinkingCodeExpiredError(ConflictError):
    """Код существует, не использован, но протух (``expires_at <= now``)."""
