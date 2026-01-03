from datetime import datetime
from typing import Self

from pydantic import Field

from beanie import Document


class AbstractDocumentModel(Document):
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    deleted_at: datetime | None = None

    async def save(self, *args, **kwargs) -> Self:
        """Сохранение модели, обновление updated_at"""

        self.updated_at = datetime.now()
        return await super().save(*args, **kwargs)

    async def delete(self, *args, **kwargs) -> Self:
        """Мягкое удаление"""

        self.deleted_at = datetime.now()
        return await self.save(*args, **kwargs)

    async def restore(self) -> Self:
        """Восстановление мягко удалённого документа"""

        self.deleted_at = None
        return await self.save()
