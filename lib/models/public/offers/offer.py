from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import StrEnum, auto
from typing import TYPE_CHECKING, Dict, Final, List, Optional, Tuple

from sqlalchemy.orm import relationship
from sqlalchemy.orm.base import Mapped
from sqlalchemy.sql.schema import CheckConstraint, Column, ForeignKey
from sqlalchemy.sql.sqltypes import (
    ARRAY,
    BigInteger,
    Boolean,
    DateTime,
    Enum,
    Integer,
    Numeric,
    String,
)

from ..._mixins import Timestamped
from ...base import Base
from ..categories.category import Category
from ..cities.city import City
from ..districts.district import District
from ..regions.region import Region
from ..users.user import User

if TYPE_CHECKING:
    from ...service.instances.instance_offer import InstanceOffer
    from ...service.workers.worker_offer import WorkerOffer
    from .offer_param import OfferParam
    from .offer_phone import OfferPhone
    from .offer_photo import OfferPhoto
    from .offer_price import OfferPrice


class PromotionOption(StrEnum):
    ad_homepage_7: Final[str] = auto()
    ad_homepage_30: Final[str] = auto()
    highlight: Final[str] = auto()
    urgent: Final[str] = auto()
    bundle_basic: Final[str] = auto()
    bundle_premium: Final[str] = auto()
    bundle_optimum: Final[str] = auto()
    topads_7: Final[str] = auto()
    topads_30: Final[str] = auto()
    pushup: Final[str] = auto()
    pushup_automatic: Final[str] = auto()


class SafedealStatus(StrEnum):
    active: Final[str] = auto()
    unactive: Final[str] = auto()


class Offer(Timestamped, Base):
    id: Mapped[int] = Column(BigInteger, primary_key=True)
    url: Mapped[str] = Column(
        String(255),
        CheckConstraint("starts_with(url, 'http')"),
        nullable=False,
    )
    title: Mapped[str] = Column(
        String(70),
        CheckConstraint("title <> ''"),
        nullable=False,
    )
    description: Mapped[str] = Column(
        String(9000),
        CheckConstraint("description <> ''"),
        nullable=False,
    )
    partner_code: Mapped[Optional[str]] = Column(
        String(64),
        CheckConstraint("partner_code IS NULL OR partner_code <> ''"),
    )
    shop_subdomain: Mapped[Optional[str]] = Column(
        String(64),
        CheckConstraint("shop_subdomain IS NULL OR shop_subdomain <> ''"),
    )
    user_id: Mapped[int] = Column(
        User.id.type,
        ForeignKey(User.id, onupdate='CASCADE', ondelete='CASCADE'),
        nullable=False,
    )
    category_id: Mapped[int] = Column(
        Category.id.type,
        ForeignKey(Category.id, onupdate='CASCADE', ondelete='RESTRICT'),
        nullable=False,
    )
    region_id: Mapped[int] = Column(
        Region.id.type,
        ForeignKey(Region.id, onupdate='CASCADE', ondelete='RESTRICT'),
        nullable=False,
    )
    city_id: Mapped[int] = Column(
        City.id.type,
        ForeignKey(City.id, onupdate='CASCADE', ondelete='RESTRICT'),
        nullable=False,
    )
    district_id: Mapped[Optional[int]] = Column(
        District.id.type,
        ForeignKey(District.id, onupdate='CASCADE', ondelete='RESTRICT'),
    )
    map_zoom: Mapped[int] = Column(
        Integer,
        CheckConstraint('map_zoom > 0 AND map_zoom <= 20'),
        nullable=False,
        default=14,
    )
    map_latitude: Mapped[Decimal] = Column(
        Numeric(8, 6),
        CheckConstraint('map_latitude >= -90 AND map_latitude <= 90'),
        nullable=False,
    )
    map_longtitude: Mapped[Decimal] = Column(
        Numeric(9, 6),
        CheckConstraint('map_longtitude >= -180 AND map_longtitude <= 180'),
        nullable=False,
    )
    map_radius: Mapped[int] = Column(
        Integer,
        CheckConstraint('map_radius >= 0 AND map_radius <= 20'),
        nullable=False,
        default=1,
    )
    safedeal_weight: Mapped[int] = Column(
        Integer,
        CheckConstraint('safedeal_weight >= 0'),
        nullable=False,
    )
    safedeal_weight_grams: Mapped[int] = Column(
        Integer,
        CheckConstraint('safedeal_weight_grams >= 0'),
        nullable=False,
    )
    safedeal_status: Mapped[SafedealStatus] = Column(
        Enum(SafedealStatus, create_constraint=True),
        nullable=False,
    )
    safedeal_allowed_quantity: Mapped[Tuple[str]] = Column(
        ARRAY(String(64), as_tuple=True),
        nullable=False,
        default=[],
    )
    promotion_options: Mapped[Tuple[str]] = Column(
        ARRAY(Enum(PromotionOption), as_tuple=True),
        nullable=False,
        default=[],
    )
    safedeal_blocked: Mapped[bool] = Column(
        Boolean(create_constraint=True),
        nullable=False,
    )
    map_show_detailed: Mapped[bool] = Column(
        Boolean(create_constraint=True),
        nullable=False,
    )
    has_phone: Mapped[bool] = Column(
        Boolean(create_constraint=True),
        nullable=False,
    )
    has_chat: Mapped[bool] = Column(
        Boolean(create_constraint=True),
        nullable=False,
    )
    has_negotiation: Mapped[bool] = Column(
        Boolean(create_constraint=True),
        nullable=False,
    )
    has_courier: Mapped[bool] = Column(
        Boolean(create_constraint=True),
        nullable=False,
    )
    is_business: Mapped[bool] = Column(
        Boolean(create_constraint=True),
        nullable=False,
    )
    is_highlighted: Mapped[bool] = Column(
        Boolean(create_constraint=True),
        nullable=False,
    )
    is_urgent: Mapped[bool] = Column(
        Boolean(create_constraint=True),
        nullable=False,
    )
    is_top_ad: Mapped[bool] = Column(
        Boolean(create_constraint=True),
        nullable=False,
    )
    is_b2c_ad_page: Mapped[bool] = Column(
        Boolean(create_constraint=True),
        nullable=False,
    )
    is_premium_ad_page: Mapped[bool] = Column(
        Boolean(create_constraint=True),
        nullable=False,
    )
    last_refresh_time: Mapped[datetime] = Column(
        DateTime(timezone=True),
        CheckConstraint('last_refresh_time > created_time'),
        nullable=False,
    )
    created_time: Mapped[datetime] = Column(
        DateTime(timezone=True),
        nullable=False,
    )
    valid_to_time: Mapped[datetime] = Column(
        DateTime(timezone=True),
        CheckConstraint('valid_to_time > created_time'),
        nullable=False,
    )
    pushup_time: Mapped[Optional[datetime]] = Column(
        DateTime(timezone=True),
        CheckConstraint(
            'pushup_time IS NULL OR pushup_time > created_time '
            'AND pushup_time <= valid_to_time'
        ),
    )
    omnibus_pushup_time: Mapped[Optional[datetime]] = Column(
        DateTime(timezone=True),
        CheckConstraint(
            'omnibus_pushup_time IS NULL OR omnibus_pushup_time > created_time '
            'AND omnibus_pushup_time <= valid_to_time'
        ),
    )

    user: Mapped['User'] = relationship(
        back_populates='offers',
        lazy='joined',
        cascade='save-update',
    )
    category: Mapped['Category'] = relationship(
        back_populates='offers',
        lazy='selectin',
        cascade='save-update',
    )
    region: Mapped['Region'] = relationship(
        back_populates='offers',
        lazy='selectin',
        cascade='save-update',
    )
    city: Mapped['City'] = relationship(
        back_populates='offers',
        lazy='selectin',
        cascade='save-update',
    )
    district: Mapped[Optional['District']] = relationship(
        back_populates='offers',
        lazy='selectin',
        cascade='save-update',
    )
    photos: Mapped[List['OfferPhoto']] = relationship(
        back_populates='offer',
        lazy='subquery',
        cascade='save-update, merge, expunge, delete, delete-orphan',
    )
    params: Mapped[List['OfferParam']] = relationship(
        back_populates='offer',
        lazy='subquery',
        cascade='save-update, merge, expunge, delete, delete-orphan',
    )
    price: Mapped[Optional['OfferPrice']] = relationship(
        back_populates='offer',
        lazy='joined',
        cascade='save-update',
    )
    phones: Mapped[List['OfferPhone']] = relationship(
        back_populates='offer',
        lazy='subquery',
        cascade='save-update, merge, expunge, delete, delete-orphan',
    )

    workers: Mapped[List['WorkerOffer']] = relationship(
        back_populates='offer',
        lazy='noload',
        cascade='save-update, merge, expunge, delete, delete-orphan',
    )
    instances: Mapped[List['InstanceOffer']] = relationship(
        back_populates='offer',
        lazy='noload',
        cascade='save-update, merge, expunge, delete, delete-orphan',
    )

    @staticmethod
    def from_json(
        user_id: int,
        region_id: int,
        city_id: int,
        district_id: Optional[int],
        item: Dict[str, object],
        /,
    ) -> Offer:
        promotion = item.get('promotion', {})
        contact = item.get('contact', {})
        map = item.get('map', {})
        safedeal = item.get('safedeal', {})
        return Offer(
            # existing
            user_id=user_id,
            region_id=region_id,
            city_id=city_id,
            district_id=district_id,
            photos=[],
            params=[],
            # basic
            id=item['id'],
            url=item['url'],
            title=item['title'],
            description=item['description'],
            category_id=item['category']['id'],
            partner_code=(item.get('partner') or {}).get('code'),
            shop_subdomain=(item.get('shop') or {}).get('subdomain'),
            # promotion
            is_business=item['business'],
            is_highlighted=promotion['highlighted'],
            is_urgent=promotion['urgent'],
            is_top_ad=promotion['top_ad'],
            is_b2c_ad_page=promotion['b2c_ad_page'],
            is_premium_ad_page=promotion['premium_ad_page'],
            promotion_options=promotion['options'],
            # contact
            has_phone=contact['phone'],
            has_chat=contact['chat'],
            has_negotiation=contact['negotiation'],
            has_courier=contact['courier'],
            # map
            map_zoom=map['zoom'],
            map_latitude=Decimal(map['lat']) if map.get('lat') else None,
            map_longtitude=Decimal(map['lon']) if map.get('lon') else None,
            map_radius=map['radius'],
            map_show_detailed=map['show_detailed'],
            # safedeal
            safedeal_weight=safedeal['weight'],
            safedeal_weight_grams=safedeal['weight_grams'],
            safedeal_status=SafedealStatus(safedeal['status'])
            if safedeal.get('status')
            else None,
            safedeal_blocked=safedeal['safedeal_blocked'],
            safedeal_allowed_quantity=safedeal.get('allowed_quantity') or [],
            # time
            last_refresh_time=datetime.fromisoformat(
                item['last_refresh_time']
            ),
            created_time=datetime.fromisoformat(item['created_time']),
            valid_to_time=datetime.fromisoformat(item['valid_to_time']),
            pushup_time=datetime.fromisoformat(item['pushup_time'])
            if item.get('pushup_time')
            else None,
            omnibus_pushup_time=datetime.fromisoformat(
                item['omnibus_pushup_time']
            )
            if item.get('omnibus_pushup_time')
            else None,
        )
