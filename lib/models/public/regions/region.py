from typing import TYPE_CHECKING, Dict, List, Self

from sqlalchemy.orm import relationship
from sqlalchemy.orm.base import Mapped
from sqlalchemy.sql.schema import CheckConstraint, Column
from sqlalchemy.sql.sqltypes import Integer, String

from ..._mixins import Timestamped
from ...base import Base

if TYPE_CHECKING:
    from ..offers.offer import Offer


class Region(Timestamped, Base):
    id: Mapped[int] = Column(Integer, primary_key=True)
    name: Mapped[str] = Column(
        String(32),
        CheckConstraint("name <> ''"),
        nullable=False,
    )
    normalized_name: Mapped[str] = Column(
        String(32),
        CheckConstraint(
            "normalized_name <> '' AND "
            'lower(normalized_name) = normalized_name'
        ),
        nullable=False,
    )

    offers: Mapped[List['Offer']] = relationship(
        back_populates='region',
        lazy='noload',
        cascade='save-update, merge, expunge, delete, delete-orphan',
    )

    @staticmethod
    def from_json(item: Dict[str, object], /) -> Self:
        return Region(
            id=item['id'],
            name=item['name'],
            normalized_name=item['normalized_name'],
        )
