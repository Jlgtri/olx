from __future__ import annotations

from decimal import Decimal
from typing import Dict, Optional

from sqlalchemy.orm import relationship
from sqlalchemy.orm.base import Mapped
from sqlalchemy.sql.schema import CheckConstraint, Column, ForeignKey
from sqlalchemy.sql.sqltypes import CHAR, Boolean, Numeric, String

from ..._mixins import Timestamped
from ...base import Base
from .offer import Offer


class OfferPrice(Timestamped, Base):
    offer_id: Mapped[int] = Column(
        Offer.id.type,
        ForeignKey(Offer.id, onupdate='CASCADE', ondelete='CASCADE'),
        primary_key=True,
    )
    name: Mapped[str] = Column(
        String(64),
        CheckConstraint("name <> ''"),
        nullable=False,
    )
    label: Mapped[str] = Column(
        String(64),
        CheckConstraint("label <> ''"),
        nullable=False,
    )
    value: Mapped[Decimal] = Column(
        Numeric(12, 2),
        CheckConstraint('value > 0'),
        nullable=False,
    )
    converted_value: Mapped[Optional[Decimal]] = Column(
        Numeric(12, 2),
        CheckConstraint('converted_value IS NULL OR converted_value > 0'),
    )
    previous_value: Mapped[Optional[Decimal]] = Column(
        Numeric(12, 2),
        CheckConstraint('previous_value IS NULL OR previous_value > 0'),
    )
    converted_previous_value: Mapped[Optional[Decimal]] = Column(
        Numeric(12, 2),
        CheckConstraint(
            'converted_previous_value IS NULL '
            'OR converted_previous_value > 0'
        ),
    )
    currency: Mapped[str] = Column(
        CHAR(3),
        CheckConstraint('upper(currency) = currency'),
        nullable=False,
    )
    converted_currency: Mapped[Optional[str]] = Column(
        CHAR(3),
        CheckConstraint(
            'converted_currency IS NULL OR '
            'upper(converted_currency) = converted_currency'
        ),
    )
    is_arranged: Mapped[bool] = Column(
        Boolean(create_constraint=True),
        nullable=False,
    )
    is_budget: Mapped[bool] = Column(
        Boolean(create_constraint=True),
        nullable=False,
    )
    is_negotiable: Mapped[bool] = Column(
        Boolean(create_constraint=True),
        nullable=False,
    )

    offer: Mapped['Offer'] = relationship(
        back_populates='price',
        lazy='noload',
        cascade='save-update',
    )

    @staticmethod
    def from_json(offer_id: int, item: Dict[str, object], /) -> OfferPrice:
        return OfferPrice(
            offer_id=offer_id,
            name=item['name'],
            label=item['value']['label'],
            value=Decimal(item['value']['value']),
            converted_value=Decimal(item['value']['converted_value'])
            if item['value']['converted_value']
            else None,
            previous_value=Decimal(item['value']['previous_value'])
            if item['value']['previous_value']
            else None,
            converted_previous_value=Decimal(
                item['value']['converted_previous_value']
            )
            if item['value']['converted_previous_value']
            else None,
            currency=item['value']['currency'],
            converted_currency=item['value']['converted_currency'],
            is_arranged=item['value']['arranged'],
            is_budget=item['value']['budget'],
            is_negotiable=item['value']['negotiable'],
        )
