from typing import Final

from sqlalchemy.dialects.postgresql.ext import ExcludeConstraint
from sqlalchemy.dialects.postgresql.ranges import INT4RANGE, Range
from sqlalchemy.orm import relationship
from sqlalchemy.orm.base import Mapped
from sqlalchemy.sql.schema import CheckConstraint, Column, ForeignKey

from ..._mixins import Timestamped
from ...base import Base, TableArgs
from ..instances.instance import Instance
from .worker import Worker


class WorkerChunk(Timestamped, Base):
    worker_chat_id: Mapped[int] = Column(
        Worker.chat_id.type,
        ForeignKey(Worker.chat_id, onupdate='CASCADE', ondelete='CASCADE'),
        primary_key=True,
    )
    range: Mapped[Range[int]] = Column(
        INT4RANGE,
        CheckConstraint('lower(range) >= 0'),
        primary_key=True,
    )
    instance_id: Mapped[int] = Column(
        Instance.id.type,
        ForeignKey(Instance.id, onupdate='CASCADE', ondelete='CASCADE'),
        nullable=False,
    )

    worker: Mapped['Worker'] = relationship(
        back_populates='chunks',
        lazy='noload',
        cascade='save-update',
    )
    instance: Mapped['Instance'] = relationship(
        back_populates='worker_chunks',
        lazy='noload',
        cascade='save-update',
    )

    __table_args__: Final[TableArgs] = (
        ExcludeConstraint((worker_chat_id, '='), (range, '&&')),
        dict(schema='service'),
    )
