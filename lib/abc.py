from abc import ABC
from dataclasses import dataclass
from logging import Logger, getLogger
from typing import Final, Optional, Self, Union

from aiogram import Bot
from aiohttp import ClientSession
from sqlalchemy.ext.asyncio.engine import AsyncEngine
from sqlalchemy.ext.asyncio.scoping import async_scoped_session
from sqlalchemy.ext.asyncio.session import AsyncSession
from sqlalchemy.orm.session import sessionmaker

from .utils.get_bind import Bind, get_bind


@dataclass(init=False, frozen=True)
class OLXABC(ABC):
    instance_id: Final[int]

    _logger: Final[Logger]
    _client: Final[Bot]
    _session: Final[ClientSession]
    _engine: Final[AsyncEngine]
    _Session: Final[
        Union[
            None,
            sessionmaker[AsyncSession],
            async_scoped_session[AsyncSession],
        ]
    ]

    def __init__(
        self: Self,
        /,
        instance_id: int,
        bind: Bind,
        client: Bot,
        session: Optional[ClientSession] = None,
        *,
        logger_name: Optional[str] = None,
    ) -> None:
        engine, Session = get_bind(bind)
        if not isinstance(client, Bot):
            raise AttributeError('Client should be a valid bot!')
        object.__setattr__(self, 'instance_id', instance_id)
        object.__setattr__(self, '_logger', getLogger(logger_name or __name__))
        object.__setattr__(self, '_client', client)
        object.__setattr__(
            self,
            '_session',
            session if isinstance(session, ClientSession) else ClientSession(),
        )
        object.__setattr__(self, '_engine', engine)
        object.__setattr__(self, '_Session', Session)

    async def run(self: Self, /) -> None:
        pass
