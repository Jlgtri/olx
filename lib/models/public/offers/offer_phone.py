from __future__ import annotations

from sqlalchemy.orm import relationship
from sqlalchemy.orm.base import Mapped
from sqlalchemy.sql.schema import CheckConstraint, Column, Computed, ForeignKey
from sqlalchemy.sql.sqltypes import BigInteger, String

from ..._mixins import Timestamped
from ...base import Base
from .offer import Offer


class OfferPhone(Timestamped, Base):
    offer_id: Mapped[int] = Column(
        Offer.id.type,
        ForeignKey(Offer.id, onupdate='CASCADE', ondelete='CASCADE'),
        primary_key=True,
    )
    number: Mapped[int] = Column(
        BigInteger,
        Computed("REGEXP_REPLACE(masked, '[^0-9]', '', 'g')::BIGINT"),
        primary_key=True,
    )
    masked: Mapped[str] = Column(
        String(30),
        CheckConstraint("masked <> '' AND lower(masked) = masked"),
        nullable=False,
    )

    offer: Mapped['Offer'] = relationship(
        back_populates='phones',
        lazy='noload',
        cascade='save-update',
    )

    @staticmethod
    def from_json(offer_id: int, phone: str, /) -> OfferPhone:
        return OfferPhone(offer_id=offer_id, masked=phone)
