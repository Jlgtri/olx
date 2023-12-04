from logging import getLogger
from time import monotonic
from typing import Dict, Final, Optional

from aiohttp import ClientSession
from anyio.to_thread import run_sync
from orjson import loads

#
logger: Final = getLogger('Fetch')


async def fetch_credentials(
    session: ClientSession,
    /,
    device_id: str,
    device_token: str,
    *,
    index: Optional[int] = None,
) -> Optional[Dict[str, object]]:
    st_time = monotonic()
    logger.debug(
        '%sFetching credentials for device `%s`...',
        f'[{index}] ' if index is not None else '',
        device_id,
    )
    async with session.post(
        'https://www.olx.ua/api/open/oauth/token/',
        json=dict(
            device_id=device_id,
            device_token=device_token,
            grant_type='device',
            scope='i2 read write v2',
            client_id='100018',
            client_secret='mo96g2Wue78VBZrhghjVJwmJk7Adn0LTs3ZI6Vdk3lgXk5hi',
        ),
    ) as response:
        if not response.ok:
            logger.exception(
                '%sException while fetching credentials for device `%s`: %s',
                f'[{index}] ' if index is not None else '',
                device_id,
                await response.text(),
            )
            return None
        content = await response.read()
    logger.info(
        '%sFetched credentials for device `%s` in %.2f second%s!',
        f'[{index}] ' if index is not None else '',
        device_id,
        f_time := monotonic() - st_time,
        '' if f_time == 1 else 's',
    )
    return await run_sync(loads, content)


async def fetch_offers(
    session: ClientSession,
    /,
    offset: int,
    limit: int,
    query: Optional[Dict[str, str]] = None,
    *,
    index: Optional[int] = None,
) -> Optional[Dict[str, object]]:
    st_time = monotonic()
    logger.debug(
        '%sFetching offers `%s-%s`...',
        f'[{index}] ' if index is not None else '',
        offset,
        offset + limit,
    )
    async with session.get(
        'https://www.olx.ua/api/v1/offers/',
        params=(query if isinstance(query, Dict) else {})
        | dict(offset=offset, limit=limit, sort_by='created_at:desc'),
    ) as response:
        if not response.ok:
            logger.exception(
                '%sException while fetching chunk `%s-%s`: %s',
                f'[{index}] ' if index is not None else '',
                offset,
                offset + limit,
                await response.text(),
            )
            return None
        content = await response.read()
    logger.info(
        '%sFetched offers `%s-%s` in %.2f second%s!',
        f'[{index}] ' if index is not None else '',
        offset,
        offset + limit,
        f_time := monotonic() - st_time,
        '' if f_time == 1 else 's',
    )
    return await run_sync(loads, content)


async def fetch_phones(
    session: ClientSession,
    /,
    offer_id: int,
    authorization_token: str,
    *,
    index: Optional[int] = None,
) -> Optional[Dict[str, object]]:
    st_time = monotonic()
    logger.debug(
        '%sFetching phones from offer `%s`...',
        f'[{index}] ' if index is not None else '',
        offer_id,
    )
    async with session.get(
        'https://www.olx.ua/api/v1/offers/%s/limited-phones/' % offer_id,
        headers={'Authorization': 'Bearer %s' % authorization_token},
    ) as response:
        if not response.ok:
            logger.exception(
                '%sException while fetching phones from offer `%s`: %s',
                f'[{index}] ' if index is not None else '',
                offer_id,
                await response.text(),
            )
            return None
        content = await response.read()
    logger.info(
        '%sFetched phones from offer `%s` in %.2f second%s!',
        f'[{index}] ' if index is not None else '',
        offer_id,
        f_time := monotonic() - st_time,
        '' if f_time == 1 else 's',
    )
    return await run_sync(loads, content)
