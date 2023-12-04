from dataclasses import dataclass
from typing import Final, Iterable, List, Optional, Self, Union

from aiogram import Bot
from aiohttp import ClientSession
from anyio import create_task_group
from sqlalchemy.sql.expression import exists, select, text

from .abc import OLXABC
from .fetch import fetch_categories
from .models.public.categories.category import Category
from .models.service.workers.worker import Worker
from .offer import OLXOffer
from .server import server
from .utils.get_bind import Bind


@dataclass(init=False, frozen=True)
class OLX(OLXABC):
    port: Final[Optional[int]]

    _worker_chat_ids: Final[Iterable[int]]

    def __init__(
        self: Self,
        /,
        instance_id: int,
        bind: Bind,
        client: Bot,
        session: Optional[ClientSession] = None,
        worker_chat_id: Union[None, int, Iterable[int]] = None,
        port: Optional[int] = None,
        *,
        logger_name: Optional[str] = None,
    ) -> None:
        super().__init__(
            instance_id,
            bind,
            client,
            session,
            logger_name=logger_name,
        )
        object.__setattr__(
            self,
            'port',
            port if isinstance(port, int) else None,
        )

        object.__setattr__(
            self,
            '_worker_chat_ids',
            tuple(worker_chat_id)
            if isinstance(worker_chat_id, Iterable)
            else (worker_chat_id,)
            if worker_chat_id
            else (),
        )

    async def run(self: Self, /) -> None:
        if not (worker_chat_ids := self._worker_chat_ids):
            if not (worker_chat_ids := await self.get_workers()):
                await self._Session.remove()
                return self._logger.exception('No workers provided!')
        self._logger.info('Started!')
        async with self._session, create_task_group() as tg:
            if self.port:
                tg.start_soon(server, self.port)
            if not await self._Session.scalar(
                select(exists(text('NULL')).select_from(Category))
            ):
                await self.process_categories()
            await self._Session.remove()
            for worker_chat_id in worker_chat_ids:
                offer = OLXOffer(
                    self.instance_id,
                    self._Session,
                    self._client,
                    self._session,
                    worker_chat_id,
                    logger_name='Offer',
                )
                tg.start_soon(offer.run)
        self._logger.info('Finished!')

    async def get_workers(self: Self, /) -> List[int]:
        statement = (
            select(Worker.chat_id)
            .filter_by(active=True)
            .order_by(Worker.created_at)
        )
        if self._worker_chat_ids:
            statement = statement.where(
                Worker.chat_id.not_in(self._worker_chat_ids)
            )
        return (
            list(self._worker_chat_ids)
            + (await self._Session.scalars(statement)).all()
        )

    async def process_categories(self: Self, /) -> None:
        if not (items := await fetch_categories(self._session)):
            raise RuntimeError('Could not fetch categories!')

        for item in sorted(items, key=lambda item: item['category_id']):
            self._Session.add(Category.from_json(item))
        try:
            await self._Session.commit()
            self._logger.info('Parsed `%s` categories!', len(items))
        except BaseException as _:
            self._logger.exception(
                'Exception while parsing category: %s',
                item,
            )
