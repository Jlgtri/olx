from logging import getLogger
from re import compile
from types import MappingProxyType
from typing import Final, Optional

from aiogram import Bot
from aiogram.types.inline_keyboard import InlineKeyboardButton as IKB
from aiogram.types.inline_keyboard import InlineKeyboardMarkup as IKM
from aiogram.types.message import Message
from aiogram.utils.exceptions import CantParseEntities

from ..models.public.offers.offer import Offer

#
logger: Final = getLogger('Export')
_currency: Final = MappingProxyType(
    {
        'AUD': '$',
        'BGN': 'лв',
        'BRL': 'R$',
        'CAD': '$',
        # 'CHF': '',
        'CNY': '¥',
        'CZK': 'Kč',
        'DKK': 'kr',
        'EUR': '€',
        'GBP': '£',
        'HKD': '$',
        'HUF': 'Ft',
        'IDR': 'Rp',
        'ILS': '₪',
        'INR': '₹',
        'ISK': 'kr',
        'JPY': '¥',
        'KRW': '₩',
        'MXN': '$',
        'MYR': 'RM',
        'NOK': 'kr',
        'NZD': '$',
        'PHP': '₱',
        'PLN': 'zł',
        'RON': 'lei',
        'SEK': 'kr',
        'SGD': '$',
        'THB': '฿',
        'TRY': '₺',
        'UAH': '₴',
        'USD': '$',
        'ZAR': 'R',
    }
)
_markdownV2: Final = compile(
    '|'.join(
        '(?<!\\\\)\\' + _
        for _ in (
            '\\',
            '_',
            '*',
            '[',
            ']',
            '(',
            ')',
            '~',
            '`',
            '>',
            '#',
            '+',
            '-',
            '=',
            '|',
            '{',
            '}',
            '.',
            '!',
        )
    )
)


def _modify(text: str, /) -> str:
    return _markdownV2.sub(lambda m: '\\' + m.group(0), text)


async def export_aiogram(
    bot: Bot,
    /,
    offer: Offer,
    chat_id: int,
) -> Optional[Message]:
    logger.info('[%s] Exporting offer `%s`...', chat_id, offer.id)
    description = offer.description.replace('<br />', '')
    about = offer.user.about.replace('<br />', '')
    params = ('*Бізнес*',) if offer.is_business else ()
    params += tuple(
        '*%s*' % _modify(param.label)
        if param.type == 'checkbox'
        else '*%s:* _%s_' % (_modify(param.name), _modify(param.label))
        for param in offer.params
    )
    category, categories = offer.category, [offer.category]
    while category.parent:
        categories.insert(0, category := category.parent)
    text = '\n'.join(
        _
        for _ in (
            r'__*[• Объявление \#%s](%s)*__' % (offer.id, offer.url),
            '• *%s*' % _modify(offer.title),
            '• *{}{}{}*'.format(
                _modify(
                    '{:,.0f} {}'.format(
                        offer.price.value,
                        _currency.get(*((offer.price.currency,) * 2)),
                    )
                )
                if offer.price.converted_currency
                else '',
                _modify(
                    ' (%s)' % offer.price.label
                    if offer.price.converted_currency
                    else offer.price.label
                ),
                ' _договорная_' if offer.has_negotiation else '',
            ).replace(',', ' ')
            if offer.price
            else '• _Цена не указана_',
            '• *%s*'
            % _modify(' > ').join(
                '[{}]({})'.format(
                    _modify(_.name),
                    'https://www.olx.ua/'
                    + '/'.join(_.code for _ in categories[:index]),
                )
                for index, _ in enumerate(categories, 1)
            ),
            '• *[{}]({})*'.format(
                _modify(
                    '%s, %s - %s'
                    % (offer.city.name, offer.district.name, offer.region.name)
                )
                if offer.district
                else _modify('%s - %s' % (offer.city.name, offer.region.name)),
                'https://maps.google.com/maps?z=%s&t=m&q=loc:%.6f+%.6f'
                % (offer.map_zoom, offer.map_latitude, offer.map_longtitude),
            ),
            '• Компания: %s' % _modify(offer.user.company_name)
            if offer.user.company_name
            else None,
            '• Код партнера: %s' % _modify(offer.partner_code)
            if offer.partner_code
            else None,
            '• Субдомен магазина: %s' % _modify(offer.shop_subdomain)
            if offer.shop_subdomain
            else None,
            '• Описание:{}'.format(
                '\n' + '_%s_' % _modify(description)
                if len(description) < 1024
                else ' _Слишком длинное_'
            ),
            '' if params else None,
            ' · '.join(params),
            '' if params else None,
            '• Контакт: %s' % _modify(offer.user.name),
            '' if offer.phones else None,
            '• Про контакт:{}'.format(
                ' _Нет информации_'
                if not about
                else '\n' + '_%s_' % _modify(about)
                if len(about) < 512
                else ' _Слишком много текста_'
            ),
            '• Номер телефона:%s'
            % (' _Отсутствует_' if not offer.phones else ''),
            *(
                r'{}\. {}'.format(index, r'*\+%s*' % phone.number)
                for index, phone in enumerate(offer.phones, 1)
            ),
            '' if offer.phones else None,
            '',
            'Дата регистрации: {}'.format(
                _modify(offer.user.created.strftime(r'%Y-%m-%d %H:%M:%S'))
                if offer.user.created
                else '_Не указана_'
            ),
            'Последний раз в сети: {}'.format(
                _modify(offer.user.last_seen.strftime(r'%Y-%m-%d %H:%M:%S'))
                if offer.user.last_seen
                else '_Не указана_'
            ),
            'Дата добавления: _%s_'
            % _modify(offer.created_time.strftime(r'%Y-%m-%d %H:%M:%S')),
            'Дата обновления: _%s_'
            % _modify(offer.last_refresh_time.strftime(r'%Y-%m-%d %H:%M:%S')),
            'Активно до: _%s_'
            % _modify(offer.valid_to_time.strftime(r'%Y-%m-%d %H:%M:%S')),
        )
        if _ is not None
    )
    try:
        return await bot.send_message(
            chat_id,
            text,
            'MarkdownV2',
            reply_markup=IKM(
                row_width=1,
                inline_keyboard=[[IKB(text='Ссылка', url=offer.url)]],
            ),
            disable_web_page_preview=True,
        )
    except CantParseEntities as _:
        print(text.replace('\n', '\\n'))
        raise
