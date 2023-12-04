from typing import TYPE_CHECKING, Final, List

from sqlalchemy.orm import relationship
from sqlalchemy.orm.base import Mapped
from sqlalchemy.sql.schema import CheckConstraint, Column
from sqlalchemy.sql.sqltypes import SmallInteger

from ..._mixins import Timestamped
from ...base import Base, TableArgs

if TYPE_CHECKING:
    from ..workers.worker_chunk import WorkerChunk
    from .instance_credential import InstanceCredential
    from .instance_offer import InstanceOffer


class Instance(Timestamped, Base):
    id: Mapped[int] = Column(
        SmallInteger,
        CheckConstraint('id >= 0'),
        primary_key=True,
    )

    credentials: Mapped[List['InstanceCredential']] = relationship(
        back_populates='instance',
        lazy='noload',
        cascade='save-update, merge, expunge, delete, delete-orphan',
    )
    offers: Mapped[List['InstanceOffer']] = relationship(
        back_populates='instance',
        lazy='noload',
        cascade='save-update, merge, expunge, delete, delete-orphan',
    )
    worker_chunks: Mapped[List['WorkerChunk']] = relationship(
        back_populates='instance',
        lazy='noload',
        cascade='save-update, merge, expunge, delete, delete-orphan',
    )

    __table_args__: Final[TableArgs] = (dict(schema='service'),)
