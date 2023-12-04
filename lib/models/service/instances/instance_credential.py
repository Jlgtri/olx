from typing import Final
from uuid import UUID

from sqlalchemy.orm import relationship
from sqlalchemy.orm.base import Mapped
from sqlalchemy.sql.schema import Column, ForeignKey
from sqlalchemy.sql.sqltypes import UUID as sa_UUID

from ..._mixins import Timestamped
from ...base import Base, TableArgs
from .instance import Instance


class InstanceCredential(Timestamped, Base):
    instance_id: Mapped[int] = Column(
        Instance.id.type,
        ForeignKey(Instance.id, onupdate='CASCADE', ondelete='CASCADE'),
        nullable=False,
    )
    credential_device_id: Mapped[UUID] = Column(sa_UUID(), primary_key=True)

    instance: Mapped['Instance'] = relationship(
        back_populates='credentials',
        lazy='noload',
        cascade='save-update',
    )

    __table_args__: Final[TableArgs] = (dict(schema='service'),)
