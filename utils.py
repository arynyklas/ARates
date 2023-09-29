from logging import Logger, getLogger as _getLogger
from telegram_bot_logger import TelegramMessageHandler, formatters as logger_formatters
from time import time
from html import escape as _html_escape
from datetime import datetime as _datetime

from typing import List, Union


def get_logger(name: str, bot_token: str, chat_ids: List[Union[int, str]], level: str) -> Logger:
    logger: Logger = _getLogger(name)

    handler: TelegramMessageHandler = TelegramMessageHandler(
        bot_token = bot_token,
        chat_ids = chat_ids,
        format_type = logger_formatters.FormatType.DOCUMENT,
        formatter = logger_formatters.TelegramHTMLTextFormatter()
    )

    logger.addHandler(
        hdlr = handler
    )

    logger.setLevel(
        level = level
    )

    return logger


def get_float_timestamp() -> float:
    return time()


def get_int_timestamp() -> int:
    return int(get_float_timestamp())


def html_escape(string: str) -> str:
    return _html_escape(
        s = string,
        quote = False
    )


def prettify_number(string: str) -> str:
    number: float = float(string)

    if number > 0:
        return "+{}".format(number)

    return str(number)


def format_datetime(datetime: _datetime) -> str:
    return datetime.strftime("%d.%m.%Y %H:%M")
