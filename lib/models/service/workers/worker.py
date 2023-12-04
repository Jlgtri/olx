from typing import TYPE_CHECKING, Dict, Final, List
from uuid import UUID

from sqlalchemy.dialects.postgresql.json import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.orm.base import Mapped
from sqlalchemy.sql.schema import CheckConstraint, Column, ForeignKey
from sqlalchemy.sql.sqltypes import BigInteger, Boolean, SmallInteger

from ..._mixins import Timestamped
from ...base import Base, TableArgs
from ..credentials.credential import Credential

if TYPE_CHECKING:
    from .worker_chunk import WorkerChunk
    from .worker_offer import WorkerOffer


class Worker(Timestamped, Base):
    chat_id: Mapped[int] = Column(BigInteger, primary_key=True)
    credential_device_id: Mapped[UUID] = Column(
        Credential.device_id.type,
        ForeignKey(
            Credential.device_id,
            onupdate='CASCADE',
            ondelete='SET NULL',
        ),
        nullable=False,
    )
    chunksize: Mapped[int] = Column(
        SmallInteger,
        CheckConstraint('chunksize > 0 AND chunksize <= 50'),
        nullable=False,
        default=40,
    )
    query: Mapped[Dict[str, str]] = Column(JSONB, nullable=False)
    active: Mapped[bool] = Column(Boolean, nullable=False, default=True)

    credential: Mapped['Credential'] = relationship(
        back_populates='workers',
        lazy='noload',
        cascade='save-update',
    )
    chunks: Mapped[List['WorkerChunk']] = relationship(
        back_populates='worker',
        lazy='noload',
        order_by='func.lower(WorkerChunk.range)',
        cascade='save-update, merge, expunge, delete, delete-orphan',
    )
    offers: Mapped[List['WorkerOffer']] = relationship(
        back_populates='worker',
        lazy='noload',
        cascade='save-update, merge, expunge, delete, delete-orphan',
    )

    __table_args__: Final[TableArgs] = (dict(schema='service'),)
