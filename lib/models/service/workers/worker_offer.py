from typing import Final

from sqlalchemy.orm import relationship
from sqlalchemy.orm.base import Mapped
from sqlalchemy.sql.schema import CheckConstraint, Column, ForeignKey
from sqlalchemy.sql.sqltypes import Integer

from ..._mixins import Timestamped
from ...base import Base, TableArgs
from ...public.offers.offer import Offer
from .worker import Worker


class WorkerOffer(Timestamped, Base):
    worker_chat_id: Mapped[int] = Column(
        Worker.chat_id.type,
        ForeignKey(Worker.chat_id, onupdate='NO ACTION', ondelete='CASCADE'),
        primary_key=True,
    )
    offer_id: Mapped[int] = Column(
        Offer.id.type,
        ForeignKey(Offer.id, onupdate='CASCADE', ondelete='CASCADE'),
        primary_key=True,
    )
    message_id: Mapped[int] = Column(
        Integer,
        CheckConstraint('message_id > 0'),
        nullable=False,
    )

    worker: Mapped['Worker'] = relationship(
        back_populates='offers',
        lazy='noload',
        cascade='save-update',
    )
    offer: Mapped['Offer'] = relationship(
        back_populates='workers',
        lazy='noload',
        cascade='save-update',
    )

    __table_args__: Final[TableArgs] = (dict(schema='service'),)
