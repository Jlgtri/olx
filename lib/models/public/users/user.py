from __future__ import annotations

from datetime import datetime
from enum import StrEnum, auto
from typing import TYPE_CHECKING, Dict, Final, List, Optional
from uuid import UUID

from sqlalchemy.orm import relationship
from sqlalchemy.orm.base import Mapped
from sqlalchemy.sql.schema import CheckConstraint, Column
from sqlalchemy.sql.sqltypes import UUID as sa_UUID
from sqlalchemy.sql.sqltypes import BigInteger, Boolean, DateTime, Enum, String

from ..._mixins import Timestamped
from ...base import Base

if TYPE_CHECKING:
    from ..offers.offer import Offer


class UserSocial(StrEnum):
    facebook: Final[str] = auto()


class User(Timestamped, Base):
    uuid: Mapped[UUID] = Column(sa_UUID, nullable=False)
    id: Mapped[int] = Column(BigInteger, primary_key=True)
    name: Mapped[str] = Column(
        String(50),
        CheckConstraint('length(name) >= 2'),
        nullable=False,
    )
    logo: Mapped[Optional[str]] = Column(
        String(511),
        CheckConstraint("logo IS NULL OR logo <> ''"),
    )
    logo_ad_page: Mapped[Optional[str]] = Column(
        String(511),
        CheckConstraint("logo_ad_page IS NULL OR logo_ad_page <> ''"),
    )
    social_network_account_type: Mapped[Optional[UserSocial]] = Column(
        Enum(UserSocial)
    )
    photo: Mapped[Optional[str]] = Column(
        String(511),
        CheckConstraint("photo IS NULL OR photo <> ''"),
    )
    seller_type: Mapped[Optional[str]] = Column(
        String(64),
        CheckConstraint("seller_type IS NULL OR seller_type <> ''"),
    )
    banner_mobile: Mapped[str] = Column(
        String(255),
        nullable=False,
        default='',
    )
    banner_desktop: Mapped[str] = Column(
        String(255),
        nullable=False,
        default='',
    )
    company_name: Mapped[str] = Column(
        String(255),
        nullable=False,
        default='',
    )
    about: Mapped[str] = Column(
        String(9000),
        nullable=False,
        default='',
    )
    other_ads_enabled: Mapped[bool] = Column(
        Boolean(create_constraint=True),
        nullable=False,
    )
    is_b2c_business_page: Mapped[bool] = Column(
        Boolean(create_constraint=True),
        nullable=False,
    )
    last_seen: Mapped[datetime] = Column(
        DateTime(timezone=True),
        nullable=False,
    )
    created: Mapped[datetime] = Column(
        DateTime(timezone=True),
        nullable=False,
    )

    offers: Mapped[List['Offer']] = relationship(
        back_populates='user',
        lazy='noload',
        cascade='save-update, merge, expunge, delete, delete-orphan',
    )

    @staticmethod
    def from_json(item: Dict[str, object], /) -> User:
        return User(
            uuid=UUID(item['uuid']),
            id=item['id'],
            name=item['name'],
            logo=item['logo'],
            logo_ad_page=item['logo_ad_page'],
            social_network_account_type=UserSocial(
                item['social_network_account_type']
            )
            if item['social_network_account_type']
            else None,
            photo=item['photo'],
            seller_type=item['seller_type'],
            banner_mobile=item['banner_mobile'],
            banner_desktop=item['banner_desktop'],
            company_name=item['company_name'],
            about=item['about'],
            other_ads_enabled=item['other_ads_enabled'],
            is_b2c_business_page=item['b2c_business_page'],
            created=datetime.fromisoformat(item['created']),
            last_seen=datetime.fromisoformat(item['last_seen']),
        )
