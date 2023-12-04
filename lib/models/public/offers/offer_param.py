from __future__ import annotations

from enum import StrEnum, auto
from typing import Dict, Final, Optional, Tuple

from sqlalchemy.orm import relationship
from sqlalchemy.orm.base import Mapped
from sqlalchemy.sql.schema import CheckConstraint, Column, ForeignKey
from sqlalchemy.sql.sqltypes import ARRAY, Enum, String

from ..._mixins import Timestamped
from ...base import Base
from .offer import Offer


class OfferType(StrEnum):
    select: Final[str] = auto()
    input: Final[str] = auto()
    checkbox: Final[str] = auto()
    checkboxes: Final[str] = auto()


class OfferParam(Timestamped, Base):
    offer_id: Mapped[int] = Column(
        Offer.id.type,
        ForeignKey(Offer.id, onupdate='CASCADE', ondelete='CASCADE'),
        primary_key=True,
    )
    key: Mapped[str] = Column(
        String(64),
        CheckConstraint("key <> '' AND lower(key) = key"),
        primary_key=True,
    )
    name: Mapped[str] = Column(
        String(64),
        CheckConstraint("name <> ''"),
        nullable=False,
    )
    type: Mapped[OfferType] = Column(
        Enum(OfferType, create_constraint=True),
        nullable=False,
    )
    value: Mapped[Tuple[str]] = Column(
        ARRAY(String(255), as_tuple=True),
        CheckConstraint('array_length(value, 1) > 0'),
        nullable=False,
    )
    label: Mapped[Optional[str]] = Column(
        String(511),
        CheckConstraint("label IS NULL OR label <> ''"),
    )

    offer: Mapped['Offer'] = relationship(
        back_populates='params',
        lazy='noload',
        cascade='save-update',
    )

    @staticmethod
    def from_json(offer_id: int, item: Dict[str, object], /) -> OfferParam:
        return OfferParam(
            offer_id=offer_id,
            key=item['key'],
            name=item['name'],
            type=item['type'],
            value=item['value']['key']
            if isinstance(item['value']['key'], list)
            else [item['value']['key']],
            label=item['value']['label'] or item['name'],
        )
