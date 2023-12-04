from asyncio import current_task
from logging import basicConfig, getLogger
from os import environ
from os import name as os_name
from sys import path
from typing import Dict, Optional

from aiogram import Bot
from aiohttp import ClientSession
from asyncclick import IntRange, group, option
from sqlalchemy.ext.asyncio.engine import create_async_engine
from sqlalchemy.ext.asyncio.scoping import async_scoped_session
from sqlalchemy.ext.asyncio.session import AsyncSession
from sqlalchemy.orm.session import sessionmaker
from sqlalchemy.pool.impl import AsyncAdaptedQueuePool
from sqlalchemy.sql.ddl import DDL

from lib import OLX
from lib.models.base import Base
from lib.models.service.credentials.credential import Credential
from lib.models.service.instances.instance import Instance
from lib.models.service.workers.worker import Worker

#
path.append('..')


@group(
    name='olx',
    invoke_without_command=True,
    context_settings=dict(token_normalize_func=lambda x: x.lower()),
)
@option(
    '-l',
    '--logging',
    help='The *logging* level used to display messges.',
    default='INFO',
)
@option(
    '-i',
    '--instance-id',
    help='The *id* of the current running instance.',
    required=True,
    type=IntRange(min=0),
)
@option(
    '-d',
    '--database-url',
    help='The *database_url* to use with SQLAlchemy.',
    callback=lambda ctx, param, value: 'postgresql+asyncpg://'
    + value.split('://')[-1].split('?')[0].strip()
    if (value := value or environ.get('DATABASE_URL'))
    else None,
)
@option(
    '-e',
    '--headers',
    help='The *headers* to use at OLX.',
    type=(str, str),
    multiple=True,
    callback=lambda ctx, param, value: dict(value),
)
@option(
    '-t',
    '--token',
    help='The Bot API *token* to create a Telegram bot session.',
    required=True,
)
@option(
    '-c',
    '--chat-id',
    help='The Telegram *chat_id* to send messages to.',
    type=int,
)
@option(
    '-q',
    '--query',
    help='The *query* to use at OLX.',
    type=(str, str),
    multiple=True,
    callback=lambda ctx, param, value: dict(value),
)
@option(
    '-u',
    '--device-id',
    help='The *device id* used for login at OLX.',
    callback=lambda ctx, param, value: value.lower() if value else None,
)
@option(
    '-p',
    '--device-token',
    help='The *device token* used for login at OLX.',
)
@option(
    '-s',
    '--chunksize',
    help='The *count* of items fetched from OLX.',
    type=IntRange(min=0, min_open=True),
)
@option(
    '--port',
    help='The *port* used for listening on HTTP requests.',
    type=IntRange(min=0, min_open=True, max=2**16, max_open=True),
)
async def cli(
    logging: str,
    instance_id: int,
    database_url: str,
    headers: Dict[str, str],
    token: Optional[str] = None,
    chat_id: Optional[int] = None,
    query: Dict[str, object] = None,
    device_id: Optional[str] = None,
    device_token: Optional[str] = None,
    chunksize: Optional[int] = None,
    port: Optional[int] = None,
) -> None:
    basicConfig(level=logging, force=True)
    getLogger('sqlalchemy.engine.Engine').propagate = False
    Session = async_scoped_session(
        sessionmaker(
            engine := create_async_engine(
                echo=False,
                url=database_url,
                poolclass=AsyncAdaptedQueuePool,
                pool_size=20,
                max_overflow=0,
                pool_recycle=3600,
                pool_pre_ping=True,
                pool_use_lifo=True,
                connect_args=dict(ssl=False, server_settings=dict(jit='off')),
                # execution_options=dict(isolation_level='SERIALIZABLE'),
            ),
            class_=AsyncSession,
            expire_on_commit=False,
            future=True,
        ),
        scopefunc=current_task,
    )
    client = Bot(token, parse_mode='MarkdownV2')
    try:
        async with engine.begin() as connection:
            for schema in {'public'} | {
                table.schema
                for table in Base.metadata.tables.values()
                if table.schema
            }:
                await connection.execute(
                    DDL(f'CREATE SCHEMA IF NOT EXISTS {schema}')
                )
            await connection.execute(
                DDL('CREATE EXTENSION IF NOT EXISTS btree_gist')
            )
            await connection.run_sync(Base.metadata.create_all)
        if device_id and device_token:
            await Session.merge(
                Credential(device_id=device_id, device_token=device_token)
            )
        if chat_id:
            chunksize = chunksize or Worker.chunksize.default.arg
            worker = await Session.merge(
                Worker(chat_id=chat_id, chunksize=chunksize, query=query)
            )
            if (device_id and device_token) and (
                worker.credential_device_id is None
            ):
                worker.credential_device_id = device_id
        await Session.merge(Instance(id=instance_id))
        await Session.commit()
        await Session.remove()
        await OLX(
            instance_id,
            Session,
            client,
            ClientSession(headers=headers),
            worker_chat_id=chat_id,
            port=port,
        ).run()
    finally:
        await engine.dispose()


if __name__ == '__main__':
    cli(
        auto_envvar_prefix='OLX',
        _anyio_backend_options=dict(use_uvloop=os_name != 'nt'),
    )
