from logging import getLogger
from time import monotonic
from typing import Dict, Final, Optional

from aiohttp import ClientSession
from anyio.to_thread import run_sync
from orjson import loads

#
logger: Final = getLogger('Fetch')


async def fetch_categories(
    session: ClientSession,
    /,
    *,
    index: Optional[int] = None,
) -> Optional[Dict[str, object]]:
    st_time = monotonic()
    logger.debug(
        '%sFetching categories...',
        f'[{index}] ' if index is not None else '',
    )
    async with session.get(
        'https://categories.olxcdn.com/v2/categories',
        params=dict(brand='olxua'),
    ) as response:
        if not response.ok:
            logger.exception(
                '%sException while fetching categories: %s',
                f'[{index}] ' if index is not None else '',
                await response.text(),
            )
            return None
        content = await response.read()
    logger.info(
        '%sFetched categories in %.2f second%s!',
        f'[{index}] ' if index is not None else '',
        f_time := monotonic() - st_time,
        '' if f_time == 1 else 's',
    )
    return await run_sync(loads, content)
