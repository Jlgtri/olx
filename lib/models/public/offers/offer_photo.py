from __future__ import annotations

from typing import Dict

from sqlalchemy.orm import relationship
from sqlalchemy.orm.base import Mapped
from sqlalchemy.sql.schema import CheckConstraint, Column, Computed, ForeignKey
from sqlalchemy.sql.sqltypes import BigInteger, SmallInteger, String

from ..._mixins import Timestamped
from ...base import Base
from .offer import Offer


class OfferPhoto(Timestamped, Base):
    offer_id: Mapped[int] = Column(
        Offer.id.type,
        ForeignKey(Offer.id, onupdate='CASCADE', ondelete='CASCADE'),
        primary_key=True,
    )
    id: Mapped[int] = Column(
        BigInteger,
        CheckConstraint('id > 0'),
        primary_key=True,
    )
    filename: Mapped[str] = Column(
        String(32),
        CheckConstraint("filename <> ''"),
        primary_key=True,
    )
    rotation: Mapped[int] = Column(
        SmallInteger,
        CheckConstraint('rotation >= 0 AND rotation < 360'),
        nullable=False,
        default=0,
    )
    width: Mapped[int] = Column(
        SmallInteger,
        CheckConstraint('width > 0'),
        nullable=False,
    )
    height: Mapped[int] = Column(
        SmallInteger,
        CheckConstraint('height > 0'),
        nullable=False,
    )
    link: Mapped[int] = Column(
        String(255),
        Computed(
            "'https://ireland.apollo.olxcdn.com:443/v1/files/' || "
            "filename || '/image;s=' || width::text || 'x' || height::text"
        ),
        nullable=False,
    )

    offer: Mapped['Offer'] = relationship(
        back_populates='photos',
        lazy='noload',
        cascade='save-update',
    )

    @staticmethod
    def from_json(offer_id: int, item: Dict[str, object], /) -> OfferPhoto:
        return OfferPhoto(
            offer_id=offer_id,
            id=item['id'],
            filename=item['filename'],
            rotation=item['rotation'],
            width=item['width'],
            height=item['height'],
        )
