from dataclasses import dataclass
from datetime import datetime, timedelta
from json import dumps
from typing import Dict, Final, List, Optional, Self, Tuple, Union

from aiogram import Bot
from aiogram.utils.exceptions import RetryAfter
from aiohttp import ClientSession
from anyio import CapacityLimiter
from anyio import create_memory_object_stream as stream
from anyio import create_task_group
from anyio import sleep as asleep
from anyio.streams.memory import MemoryObjectReceiveStream as Receiver
from anyio.streams.memory import MemoryObjectSendStream as Sender
from dateutil.tz.tz import tzlocal
from sqlalchemy.dialects.postgresql.ranges import Range
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload
from sqlalchemy.sql.expression import delete, exists, select, text

from ..abc import OLXABC
from ..models.public.offers.offer import Offer
from ..models.service.credentials.credential import Credential
from ..models.service.instances.instance_credential import InstanceCredential
from ..models.service.workers.worker import Worker
from ..models.service.workers.worker_chunk import WorkerChunk
from ..models.service.workers.worker_offer import WorkerOffer
from ..utils.get_bind import Bind
from ..utils.wrap_exc import wrap_exc
from .export import export_aiogram
from .fetch import fetch_credentials, fetch_offers
from .parse import parse_offer


@dataclass(init=False, frozen=True)
class OLXOffer(OLXABC):
    worker_chat_id: Final[int]

    _limiter: Final[CapacityLimiter]
    _phone_limiter: Final[CapacityLimiter]

    def __init__(
        self: Self,
        /,
        instance_id: int,
        bind: Bind,
        client: Bot,
        session: Optional[ClientSession] = None,
        worker_chat_id: Union[None, int] = None,
        workers: Optional[int] = None,
        phone_workers: Optional[int] = None,
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
        if not isinstance(worker_chat_id, int):
            raise AttributeError('`worker_chat_id` should be an integer!')

        object.__setattr__(self, 'worker_chat_id', worker_chat_id)
        object.__setattr__(
            self,
            '_limiter',
            CapacityLimiter(workers if isinstance(workers, int) else 1),
        )
        object.__setattr__(
            self,
            '_phone_limiter',
            CapacityLimiter(
                phone_workers
                if isinstance(phone_workers, int)
                else self._limiter.total_tokens
            ),
        )

    async def run(self: Self, /) -> None:
        self._logger.info('[%s] Started offer!', self.worker_chat_id)
        if (credential := await self.get_credential()) is None:
            await self._Session.remove()
            return self._logger.warning(
                '[%s] There are no valid credentials!', self.worker_chat_id
            )
        await self._Session.remove()

        # parse_sender, parse_receiver = stream(
        #     0,
        #     Tuple[WorkerChunk, List[Dict[str, object]]],
        # )
        # offer_sender, offer_receiver = stream(
        #     0,
        #     Tuple[InstanceOffer, Offer],
        # )
        # offer_parse_sender, offer_parse_receiver = stream(
        #     0, Tuple[InstanceOffer, Offer, List[Dict[str, object]]]
        # )
        export_sender, export_receiver = stream(0, int)
        async with (
            # parse_sender,
            # parse_receiver,
            # offer_sender,
            # offer_receiver,
            # offer_parse_sender,
            # offer_parse_receiver,
            export_sender,
            export_receiver,
            create_task_group() as tg,
        ):
            # for _ in range(self._limiter.total_tokens):
            tg.start_soon(wrap_exc(self.process), export_sender)
            # for _ in range(self._phone_limiter.total_tokens):
            #     tg.start_soon(
            #         wrap_exc(self.fetch_phones),
            #         offer_receiver.clone(),
            #         offer_parse_sender.clone(),
            #         credential,
            #     )
            # tg.start_soon(
            #     wrap_exc(self.parse_offers),
            #     parse_receiver,
            #     export_sender,
            # )
            # tg.start_soon(
            #     wrap_exc(self.parse_phones),
            #     offer_parse_receiver,
            #     export_sender,
            # )
            tg.start_soon(wrap_exc(self.export), export_receiver)

        self._logger.info('[%s] Finished offer!', self.worker_chat_id)

    async def process(self: Self, export_sender: Sender[int], /) -> None:
        async with export_sender:
            while True:
                worker = await self._Session.get(
                    Worker,
                    self.worker_chat_id,
                    options=(selectinload(Worker.chunks),),
                )
                for offset in range(
                    0,
                    1000 + worker.chunksize - 1,
                    worker.chunksize,
                ):
                    chunk_range = Range(offset, offset + worker.chunksize)
                    chunk, is_processing = None, False
                    for _chunk in worker.chunks:
                        if _chunk.range.contains(chunk_range):
                            if _chunk.instance_id == self.instance_id:
                                chunk = _chunk
                            elif (
                                datetime.now(tzlocal()) - _chunk.updated_at
                            ) < timedelta(minutes=1):
                                is_processing = True
                            else:
                                await self._Session.delete(_chunk)
                                await self._Session.commit()
                    if not is_processing and chunk is None:
                        chunk = WorkerChunk(
                            worker_chat_id=self.worker_chat_id,
                            range=chunk_range,
                            instance_id=self.instance_id,
                        )
                        self._Session.add(chunk)
                        await self._Session.commit()
                    if not is_processing:
                        data = await fetch_offers(
                            self._session,
                            chunk.range.lower,
                            chunk.range.upper - chunk.range.lower,
                            worker.query,
                            index=self.worker_chat_id,
                        )
                        # if offer.has_phone:
                        # with suppress(BaseException):
                        #     async with self._Session.begin_nested():
                        #         self._Session.add(
                        #             instance_offer := InstanceOffer(
                        #                 instance_id=self.instance_id,
                        #                 offer_id=offer.id,
                        #             )
                        #         )
                        # offer = await self._Session.get(
                        #     Offer, offer.id
                        # )
                        # await offer_sender.send(
                        #     (instance_offer, offer)
                        # )

                        offers: List[Offer] = []
                        for item in data['data']:
                            try:
                                if offer := await parse_offer(
                                    self._Session,
                                    item,
                                    index=self.worker_chat_id,
                                ):
                                    offers.append(offer)
                            except IntegrityError as _:
                                self._logger.warning(
                                    '[%s] Invalid offer: %s',
                                    self.worker_chat_id,
                                    dumps(item, indent=4),
                                )
                                continue
                        processed_offer_ids = await self._Session.scalars(
                            select(WorkerOffer.offer_id).where(
                                WorkerOffer.worker_chat_id
                                == self.worker_chat_id,
                                WorkerOffer.offer_id.in_(
                                    [_.id for _ in offers]
                                ),
                            )
                        )
                        processed_offer_ids = set(processed_offer_ids.all())
                        await self._Session.remove()
                        for offer in offers:
                            if offer.id not in processed_offer_ids:
                                await export_sender.send(offer.id)
                            else:
                                self._logger.info(
                                    '[%s] Skipped exporting offer `%s`!',
                                    self.worker_chat_id,
                                    offer.id,
                                )
                        await self._Session.execute(
                            delete(WorkerChunk).filter_by(
                                worker_chat_id=chunk.worker_chat_id,
                                range=chunk.range,
                            )
                        )
                        await self._Session.commit()
                        await self._Session.remove()
                        if len(processed_offer_ids) == len(offers):
                            await asleep(60)
                            break

    # async def fetch_phones(
    #     self: Self,
    #     offer_receiver: Receiver[Tuple[InstanceOffer, Offer]],
    #     offer_parse_sender: Sender[
    #         Tuple[InstanceOffer, Offer, List[Dict[str, object]]]
    #     ],
    #     /,
    #     credential: Credential,
    # ) -> None:
    #     async with offer_receiver, offer_parse_sender, self._phone_limiter:
    #         async for instance_offer, offer in offer_receiver:
    #             items = await fetch_phones(
    #                 self._session,
    #                 offer.id,
    #                 credential.access_token,
    #                 index=self.worker_chat_id,
    #             )
    #             await offer_parse_sender.send(
    #                 instance_offer, offer, items['data']
    #             )

    # async def parse_phones(
    #     self: Self,
    #     phone_parse_receiver: Receiver[
    #         Tuple[InstanceOffer, Offer, List[Dict[str, object]]]
    #     ],
    #     export_sender: Sender[int],
    #     /,
    # ) -> None:
    #     async with phone_parse_receiver, export_sender:
    #         async for instance_offer, offer, items in phone_parse_receiver:
    #             for item in items:
    #                 try:
    #                     async with self._Session.begin_nested():
    #                         self._Session.add(
    #                             OfferPhone.from_json(offer.id, item)
    #                         )
    #                 except BaseException:
    #                     self._logger.warning(
    #                         '[%s] Invalid phone from offer `%s`: %s',
    #                         self.worker_chat_id,
    #                         offer.id,
    #                         dumps(item, indent=4),
    #                     )
    #             await self._Session.delete(instance_offer)
    #             await self._Session.commit()
    #             await self._Session.remove()
    #             if offer.phones:
    #                 await export_sender.send(offer)
    #             else:
    #                 self._logger.info(
    #                     '[%s] Skipped exporting offer `%s` no phone provided!',
    #                     self.worker_chat_id,
    #                     offer.id,
    #                 )

    async def export(self: Self, export_receiver: Receiver[int], /) -> None:
        async with export_receiver:
            async for offer_id in export_receiver:
                offer = await self._Session.get(Offer, offer_id)
                message_id = None
                while True:
                    try:
                        message = await export_aiogram(
                            self._client, offer, self.worker_chat_id
                        )
                        if message is not None:
                            message_id = message.message_id
                        break
                    except RetryAfter as exception:
                        self._logger.warning(
                            '[%s] Exporting cooldown for `%.0f` second%s!',
                            self.worker_chat_id,
                            exception.timeout,
                            '' if exception.timeout == 1 else 's',
                        )
                        await asleep(exception.timeout)
                    except BaseException as _:
                        self._logger.exception(_)
                        break

                if message_id is not None:
                    try:
                        self._Session.add(
                            WorkerOffer(
                                worker_chat_id=self.worker_chat_id,
                                offer_id=offer.id,
                                message_id=message_id,
                            )
                        )
                        await self._Session.commit()
                    except IntegrityError as exception:
                        if exception.orig.pgcode != '23505':
                            raise
                await self._Session.remove()
                await asleep(1)

    async def get_credential(self: Self, /) -> Optional[Credential]:
        credential_devices = []
        worker = await self._Session.get(Worker, self.worker_chat_id)
        if worker.credential_device_id is not None:
            credential = await self._Session.get(
                Credential, worker.credential_device_id
            )
            if not credential.expired:
                return credential
            credential_devices.append(
                (credential.device_id, credential.device_token)
            )
        result = await self._Session.execute(
            select(Credential.device_id, Credential.device_token)
            .where(
                ~exists(text('NULL')).where(
                    Worker.credential_device_id == Credential.device_id
                )
            )
            .order_by(Credential.expires_at)
        )
        for device_id, device_token in credential_devices + result.all():
            instance_credential = await self._Session.merge(
                InstanceCredential(
                    instance_id=self.instance_id,
                    credential_device_id=device_id,
                )
            )
            await self._Session.commit()

            try:
                if item := await fetch_credentials(
                    self._session,
                    str(device_id),
                    device_token,
                    index=self.worker_chat_id,
                ):
                    worker.credential = await self._Session.merge(
                        Credential.from_json(device_id, device_token, item)
                    )
                    await self._Session.commit()
                    self._logger.info(
                        '[%s] Parsed credential for device `%s`!',
                        self.worker_chat_id,
                        str(device_id),
                    )
                    return credential
            except IntegrityError as _:
                await self._Session.rollback()
                continue
            finally:
                await self._Session.delete(instance_credential)
                await self._Session.commit()
        return None
