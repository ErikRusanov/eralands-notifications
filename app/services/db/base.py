"""base — универсальный CRUD-сервис поверх ORM-модели.

Сервис работает строго со своей ORM-моделью и принимает данные в виде
Pydantic-схем, тех же, что используются в API-слое. Это убирает
ручную сборку dict-ов и оставляет валидацию на схеме.

Конкретные сервисы наследуются от ``BaseDBService`` и фиксируют свою
модель через атрибут класса:

    class ClientService(BaseDBService[Client]):
        model = Client

Сервис только flush-ит изменения. Управлять транзакцией (commit/rollback)
должен вызывающий код, обычно через зависимость сессии.
"""

import uuid
from typing import ClassVar, Generic, TypeVar

from pydantic import BaseModel as PydanticModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import BaseModel as ORMModel

ModelT = TypeVar("ModelT", bound=ORMModel)


class BaseDBService(Generic[ModelT]):
    """Универсальный CRUD над ORM-моделью на async-сессии.

    Атрибуты класса:
        model: ORM-модель, с которой работает сервис. Задаётся в наследнике.
    """

    model: ClassVar[type[ORMModel]]

    def __init__(self, session: AsyncSession) -> None:
        """Инициализирует сервис на переданной async-сессии.

        Аргументы:
            session: Активная ``AsyncSession`` SQLAlchemy.
        """
        self.session = session

    async def get(self, id_: uuid.UUID) -> ModelT | None:
        """Возвращает объект по primary key или ``None``, если такого нет.

        Аргументы:
            id_: Идентификатор записи.
        """
        return await self.session.get(self.model, id_)

    async def create(self, data: PydanticModel) -> ModelT:
        """Создаёт новый объект из данных схемы и flush-ит сессию.

        Аргументы:
            data: Pydantic-схема со всеми обязательными полями модели.

        Возвращает:
            Созданный ORM-объект, привязанный к сессии.
        """
        instance = self.model(**data.model_dump())
        self.session.add(instance)
        await self.session.flush()
        return instance

    async def get_or_create(
        self,
        data: PydanticModel,
        *,
        by: tuple[str, ...],
    ) -> tuple[ModelT, bool]:
        """Возвращает существующий объект по полям ``by`` либо создаёт новый.

        Поиск ведётся по подмножеству полей схемы, перечисленных в ``by``.
        Если объект не найден, создаётся новый из всех полей схемы
        (``model_dump()``).

        Аргументы:
            data: Pydantic-схема с данными для поиска и/или создания.
            by: Имена полей схемы, по которым ведётся поиск существующей записи.

        Возвращает:
            Кортеж ``(instance, created)``, где ``created=True``, если объект
            был создан, и ``False``, если найден существующий.
        """
        lookup = {field: getattr(data, field) for field in by}
        stmt = select(self.model).filter_by(**lookup)
        instance = (await self.session.scalars(stmt)).one_or_none()
        if instance is not None:
            return instance, False

        instance = self.model(**data.model_dump())
        self.session.add(instance)
        await self.session.flush()
        return instance, True

    async def update(self, instance: ModelT, data: PydanticModel) -> ModelT:
        """Обновляет поля ``instance`` значениями из ``data``.

        Применяются только явно установленные поля схемы
        (``model_dump(exclude_unset=True)``), чтобы можно было слать частичные
        патчи и не затирать остальные значения дефолтами схемы.

        Аргументы:
            instance: ORM-объект, прикреплённый к текущей сессии.
            data: Pydantic-схема с новыми значениями полей.

        Возвращает:
            Тот же ``instance`` с применёнными изменениями.
        """
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(instance, field, value)
        await self.session.flush()
        return instance

    async def delete(self, instance: ModelT) -> None:
        """Удаляет объект из БД.

        Аргументы:
            instance: ORM-объект, прикреплённый к текущей сессии.
        """
        await self.session.delete(instance)
        await self.session.flush()
