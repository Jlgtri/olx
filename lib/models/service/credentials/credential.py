from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Dict, Final, List, Optional, Self, Type
from uuid import UUID

from dateutil.tz.tz import tzlocal
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import relationship
from sqlalchemy.orm.base import Mapped
from sqlalchemy.sql.elements import ColumnElement
from sqlalchemy.sql.functions import now
from sqlalchemy.sql.schema import CheckConstraint, Column
from sqlalchemy.sql.sqltypes import CHAR
from sqlalchemy.sql.sqltypes import UUID as sa_UUID
from sqlalchemy.sql.sqltypes import DateTime, String

from ..._mixins import Timestamped
from ...base import Base, TableArgs

if TYPE_CHECKING:
    from ..workers.worker import Worker


class Credential(Timestamped, Base):
    device_id: Mapped[UUID] = Column(sa_UUID(), primary_key=True)
    device_token: Mapped[str] = Column(
        String(255),
        CheckConstraint("device_token <> ''"),
        nullable=False,
    )
    access_token: Mapped[Optional[str]] = Column(
        CHAR(40),
        CheckConstraint(
            'access_token IS NULL OR '
            "access_token <> '' AND lower(access_token) = access_token"
        ),
    )
    refresh_token: Mapped[Optional[str]] = Column(
        CHAR(40),
        CheckConstraint(
            'refresh_token IS NULL OR '
            "refresh_token <> '' AND lower(refresh_token) = refresh_token"
        ),
    )
    expires_at: Mapped[Optional[datetime]] = Column(DateTime(timezone=True))

    workers: Mapped[List['Worker']] = relationship(
        back_populates='credential',
        lazy='noload',
        cascade='save-update, merge, expunge, delete, delete-orphan',
    )

    @hybrid_property
    def expired(self: Self, /) -> bool:
        return self.expires_at is None or self.expires_at < datetime.now(
            tzlocal()
        )

    @expired.expression
    def expired(cls: Type[Self], /) -> ColumnElement[bool]:
        return cls.expires_at.is_(None) | (cls.expires_at < now())

    __table_args__: Final[TableArgs] = (dict(schema='service'),)

    @staticmethod
    def from_json(
        device_id: str,
        device_token: str,
        item: Dict[str, object],
        /,
    ) -> Self:
        return Credential(
            device_id=device_id,
            device_token=device_token,
            access_token=item['access_token'],
            refresh_token=item['refresh_token'],
            expires_at=datetime.now(tzlocal())
            + timedelta(seconds=item['expires_in']),
        )
