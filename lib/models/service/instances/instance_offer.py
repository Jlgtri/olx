from typing import Final

from sqlalchemy.orm import relationship
from sqlalchemy.orm.base import Mapped
from sqlalchemy.sql.schema import Column, ForeignKey

from ..._mixins import Timestamped
from ...base import Base, TableArgs
from ...public.offers.offer import Offer
from .instance import Instance


class InstanceOffer(Timestamped, Base):
    instance_id: Mapped[int] = Column(
        Instance.id.type,
        ForeignKey(Instance.id, onupdate='CASCADE', ondelete='CASCADE'),
        nullable=False,
    )
    offer_id: Mapped[int] = Column(
        Offer.id.type,
        ForeignKey(Offer.id, onupdate='CASCADE', ondelete='CASCADE'),
        primary_key=True,
    )

    instance: Mapped['Instance'] = relationship(
        back_populates='offers',
        lazy='noload',
        cascade='save-update',
    )
    offer: Mapped['Offer'] = relationship(
        back_populates='instances',
        lazy='noload',
        cascade='save-update',
    )

    __table_args__: Final[TableArgs] = (dict(schema='service'),)
