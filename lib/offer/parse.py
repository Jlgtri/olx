from logging import getLogger
from typing import Dict, Final, Optional

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio.scoping import async_scoped_session
from sqlalchemy.ext.asyncio.session import AsyncSession

from ..models.base import Base
from ..models.public.cities.city import City
from ..models.public.districts.district import District
from ..models.public.offers.offer import Offer
from ..models.public.offers.offer_param import OfferParam
from ..models.public.offers.offer_photo import OfferPhoto
from ..models.public.offers.offer_price import OfferPrice
from ..models.public.regions.region import Region
from ..models.public.users.user import User

#
logger: Final = getLogger('Parse')


async def parse_offer(
    Session: async_scoped_session[AsyncSession],
    /,
    item: Dict[str, object],
    *,
    index: Optional[object] = None,
) -> Optional[Offer]:
    def log(name: str, key: object, /, *, skip: bool = False) -> None:
        _index = '[%s] ' % index if index is not None else ''
        _type = 'Skipped' if skip else 'Parsed'
        logger.debug('%s%s %s `%s`!', _index, _type, name, key)

    async def parse(item: Base, name: str, key: object, /) -> None:
        try:
            async with Session.begin_nested():
                Session.add(item)
            log(name, key)
        except IntegrityError as exception:
            if name == 'offer':
                pass
            if exception.orig.pgcode != '23505':
                raise
            log(name, key, skip=True)

    user = User.from_json(item['user'])
    await parse(user, 'user', user.id)
    location = item.get('location', {})
    region = Region.from_json(location['region'])
    await parse(region, 'region', region.id)
    city = City.from_json(location['city'])
    await parse(city, 'city', city.id)
    if district := location.get('district'):
        district = District.from_json(district)
        await parse(district, 'district', district.id)

    offer = Offer.from_json(
        user.id,
        region.id,
        city.id,
        district.id if district else None,
        item,
    )
    await parse(offer, 'offer', offer.id)
    await Session.commit()

    for photo in item.get('photos', []):
        photo = OfferPhoto.from_json(offer.id, photo)
        await parse(photo, 'photo', photo.id)
    for param in item.get('params', []):
        if param['type'] == 'price':
            price = OfferPrice.from_json(offer.id, param)
            await parse(price, 'price', offer.id)
        else:
            param = OfferParam.from_json(offer.id, param)
            await parse(param, 'param', param.key)
    await Session.commit()
    return offer
