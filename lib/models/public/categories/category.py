from __future__ import annotations

from enum import StrEnum, auto
from typing import TYPE_CHECKING, Dict, Final, List, Optional

from sqlalchemy.orm import relationship
from sqlalchemy.orm.base import Mapped
from sqlalchemy.sql.schema import CheckConstraint, Column, ForeignKey
from sqlalchemy.sql.sqltypes import Boolean, Enum, SmallInteger, String

from ..._mixins import Timestamped
from ...base import Base

if TYPE_CHECKING:
    from ..offers.offer import Offer


class CategoryType(StrEnum):
    goods: Final[str] = auto()
    job: Final[str] = auto()
    automotive: Final[str] = auto()
    real_estate: Final[str] = auto()
    electronics: Final[str] = auto()
    services: Final[str] = auto()
    other: Final[str] = auto()


class CategoryViewType(StrEnum):
    gallery: Final[str] = auto()
    list: Final[str] = auto()
    grid: Final[str] = auto()


class Category(Timestamped, Base):
    parent_id: Mapped[Optional[int]] = Column(
        SmallInteger,
        ForeignKey('categories.id', onupdate='CASCADE', ondelete='CASCADE'),
    )
    id: Mapped[int] = Column(
        SmallInteger,
        CheckConstraint('id > 0'),
        primary_key=True,
    )
    name: Mapped[str] = Column(
        String(255),
        CheckConstraint("name <> ''"),
        nullable=False,
    )
    code: Mapped[str] = Column(
        String(255),
        CheckConstraint("code <> '' AND lower(code) = code"),
        nullable=False,
    )
    type: Mapped[CategoryType] = Column(Enum(CategoryType), nullable=False)
    view_type: Mapped[CategoryViewType] = Column(
        Enum(CategoryViewType),
        nullable=False,
    )
    position: Mapped[int] = Column(
        SmallInteger,
        CheckConstraint('position > 0'),
        nullable=False,
    )
    max_photos: Mapped[int] = Column(
        SmallInteger,
        CheckConstraint('max_photos >= 0'),
        nullable=False,
    )
    is_addable: Mapped[bool] = Column(
        Boolean(create_constraint=True),
        nullable=False,
    )
    is_searchable: Mapped[bool] = Column(
        Boolean(create_constraint=True),
        nullable=False,
    )
    is_offer_seekable: Mapped[bool] = Column(
        Boolean(create_constraint=True),
        nullable=False,
    )
    is_business: Mapped[bool] = Column(
        Boolean(create_constraint=True),
        nullable=False,
    )

    offers: Mapped[List['Offer']] = relationship(
        back_populates='category',
        lazy='noload',
        cascade='save-update, merge, expunge, delete, delete-orphan',
    )
    parent: Mapped[Optional['Category']] = relationship(
        back_populates='children',
        lazy='joined',
        join_depth=4,
        remote_side=[id],
        cascade='save-update',
    )
    children: Mapped[List['Category']] = relationship(
        back_populates='parent',
        lazy='noload',
        join_depth=1,
        cascade='save-update, merge, expunge, delete, delete-orphan',
    )

    @staticmethod
    def from_json(item: Dict[str, object], /) -> Category:
        return Category(
            parent_id=item['parent'] or None,
            id=item['category_id'],
            name=item['name'],
            code=item['code'],
            type=CategoryType(item['type'] or 'other'),
            view_type=CategoryViewType(item['view_type']),
            position=item['position'],
            max_photos=item['max_photos'],
            is_addable=item['is_addable'],
            is_searchable=item['is_searchable'],
            is_offer_seekable=item['is_offer_seekable'],
            is_business=item['is_business'],
        )
