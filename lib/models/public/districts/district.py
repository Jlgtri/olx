from __future__ import annotations

from typing import TYPE_CHECKING, Dict, List

from sqlalchemy.orm import relationship
from sqlalchemy.orm.base import Mapped
from sqlalchemy.sql.schema import CheckConstraint, Column
from sqlalchemy.sql.sqltypes import Integer, String

from ..._mixins import Timestamped
from ...base import Base

if TYPE_CHECKING:
    from ..offers.offer import Offer


class District(Timestamped, Base):
    id: Mapped[int] = Column(Integer, primary_key=True)
    name: Mapped[str] = Column(
        String(32),
        CheckConstraint("name <> ''"),
        nullable=False,
    )

    offers: Mapped[List['Offer']] = relationship(
        back_populates='district',
        lazy='noload',
        cascade='save-update, merge, expunge, delete, delete-orphan',
    )

    @staticmethod
    def from_json(item: Dict[str, object], /) -> District:
        return District(id=item['id'], name=item['name'])
