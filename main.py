from aiogram import Dispatcher, Bot, enums, filters, types, exceptions

from io import BytesIO
from pytz import utc as utc_timezone
from datetime import datetime
from asyncio import sleep, create_task

from coingecko import CoinGecko
from basic_data import TEXTS
from config import config

import utils

from typing import Optional, Tuple, Dict, AsyncGenerator, List


dispatcher: Dispatcher = Dispatcher()

bot: Bot = Bot(
    token = config.bot_token,
    parse_mode = enums.ParseMode.HTML
)


coingecko: CoinGecko = CoinGecko(
    vs_currency = config.coingecko.vs_currency,
    chart_days = config.coingecko.chart_days,
    proxies = config.proxies
)


CAN_STARTUP: bool = False
DEFAULT_MESSAGE: Optional[str] = None


def parse_price(current_prices: Dict[str, float], price_change_percentages: Dict[str, float], currency_name: str, numbers_after: int) -> Tuple[str, str]:
    return (
        format(
            current_prices[currency_name],
            ".{numbers_after}f".format(
                numbers_after = numbers_after
            )
        ),
        utils.prettify_number(
            string = format(
                price_change_percentages[currency_name],
                ".1f"
            )
        )
    )


class CustomBufferedInputFile(types.InputFile):
    def __init__(self, buffered_file: BytesIO, filename: str, chunk_size: int = types.input_file.DEFAULT_CHUNK_SIZE):
        super().__init__(filename=filename, chunk_size=chunk_size)

        self.buffered_file: BytesIO = buffered_file

    async def read(self, bot: Bot) -> AsyncGenerator[bytes, None]:
        while chunk := self.buffered_file.read(self.chunk_size):
            yield chunk


async def edit_default_message() -> None:
    try:
        await bot.edit_message_text(
            chat_id = config.main_channel_id,
            message_id = config.main_channel_message_id,
            text = DEFAULT_MESSAGE,
            disable_web_page_preview = True
        )

    except exceptions.TelegramAPIError:
        pass


async def coingecko_prices_checker() -> None:
    global DEFAULT_MESSAGE, CAN_STARTUP

    vs_currency_upper: str = config.coingecko.vs_currency.upper()

    started_at: float

    started_at = utils.get_float_timestamp()

    skipped_time: float = started_at % config.coingecko.prices_checker_delay

    if skipped_time > 0:
        await sleep(config.coingecko.prices_checker_delay - skipped_time)

    while True:
        started_at = utils.get_float_timestamp()

        updated_prices: Dict[str, float] = {}

        for coin_name, (channel_id, _) in config.channels.items():
            coin_code: str = config.coins[coin_name]

            market_data: dict = await coingecko.get_market_data(
                coin_code = coin_code
            )

            dt_now: datetime = datetime.now(
                tz = utc_timezone
            )

            parse_prices: Dict[str, Tuple[str, int]] = config.parse_prices.copy()

            if coin_name in parse_prices:
                del parse_prices[coin_name]

            current_prices: Dict[str, float] = market_data["current_price"]
            price_change_percentages: Dict[str, float] = market_data["price_change_percentage_24h_in_currency"]

            prices_and_percentages: List[str] = []

            for currency_name_upper, (currency_name_lower, numbers_after) in parse_prices.items():
                currency_price: str
                currency_persentage: str

                currency_price, currency_persentage = parse_price(
                    current_prices = current_prices,
                    price_change_percentages = price_change_percentages,
                    currency_name = currency_name_lower,
                    numbers_after = numbers_after
                )

                prices_and_percentages.append(
                    TEXTS.price.format(
                        currency_name = currency_name_upper,
                        currency_price = currency_price,
                        currency_persentage = currency_persentage
                    )
                )

            await bot.send_photo(
                chat_id = channel_id,
                photo = CustomBufferedInputFile(
                    buffered_file = (
                        await coingecko.create_plot(
                            coin_code = coin_code,
                            title = "{coin_name}-{vs_currency}".format(
                                coin_name = coin_name,
                                vs_currency = vs_currency_upper
                            )
                        )
                    ),
                    filename = config.upload_filename
                ),
                caption = TEXTS.channel_notify.format(
                    prices = "\n".join(prices_and_percentages),
                    coin_code = coin_code,
                    main_channel_url = config.main_channel_url,
                    main_channel_title = config.main_channel_title,
                    time = dt_now.strftime("%H:%M"),
                    date = dt_now.strftime("%d.%m.%Y")
                )
            )

            updated_prices[coin_name] = market_data["current_price"][config.coingecko.vs_currency]

        DEFAULT_MESSAGE = TEXTS.default_message.format(
            channels = "\n".join([
                TEXTS.channel.format(
                    coin_name = coin_name,
                    channel_url = channel_url,
                    channel_price = TEXTS.channel_price.format(
                        currency_price = format(
                            updated_prices[coin_name],
                            ".{numbers_after}f".format(
                                numbers_after = config.parse_prices[vs_currency_upper][1]
                            )
                        ),
                        vs_currency = vs_currency_upper
                    )
                )
                for coin_name, (_, channel_url) in config.channels.items()
            ]),
            main_channel_url = config.main_channel_url,
            main_channel_title = config.main_channel_title
        )

        await edit_default_message()

        CAN_STARTUP = True

        sleep_time: float = config.coingecko.prices_checker_delay - (utils.get_float_timestamp() - started_at)

        if sleep_time > 0:
            await sleep(sleep_time)


@dispatcher.message(filters.Command("start"))
async def start_handler(message: types.Message) -> None:
    await message.answer(
        text = DEFAULT_MESSAGE,
        disable_web_page_preview = True
    )


@dispatcher.startup()
async def on_startup() -> None:
    create_task(coingecko_prices_checker())

    while not CAN_STARTUP:
        await sleep(1)


@dispatcher.shutdown()
async def on_shutdown() -> None:
    pass


if __name__ == "__main__":
    dispatcher.run_polling(bot)
