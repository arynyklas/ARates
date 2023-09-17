from aiogram import Dispatcher, Bot, enums, filters, types, exceptions

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from pytz import utc as utc_timezone
from datetime import datetime

from coingecko import CoinGecko
from basic_data import TEXTS
from utils import prettify_number
from config import config

from typing import Tuple, Dict, List


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


def parse_price(current_prices: Dict[str, float], price_change_percentages: Dict[str, float], currency_name: str, numbers_after: int) -> Tuple[str, str]:
    return (
        format(
            current_prices[currency_name],
            ".{numbers_after}f".format(
                numbers_after = numbers_after
            )
        ),
        prettify_number(
            string = format(
                price_change_percentages[currency_name],
                ".1f"
            )
        )
    )


async def exchange_checker() -> None:
    for coin_name, (channel_id, _) in config.channels.items():
        print(f"{coin_name} ({channel_id})")

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

        caption: str = TEXTS.channel_notify.format(
            prices = "\n".join(prices_and_percentages),
            coin_code = coin_code,
            main_channel_url = config.main_channel_url,
            main_channel_title = config.main_channel_title,
            time = dt_now.strftime("%H:%M"),
            date = dt_now.strftime("%d.%m.%Y")
        )

        await bot.send_photo(
            chat_id = channel_id,
            photo = types.BufferedInputFile(
                file = (
                    await coingecko.create_plot(
                        coin_code = coin_code,
                        title = "{coin_name}-USD".format(
                            coin_name = coin_name
                        )
                    )
                ).read(),
                filename = "photo.png"
            ),
            caption = caption
        )


@dispatcher.message(filters.Command("start"))
async def start_handler(message: types.Message) -> None:
    await message.answer(
        text = TEXTS.start.format(
            channels = "\n".join([
                TEXTS.channel.format(
                    coin_name = coin_name,
                    channel_url = channel_url
                )
                for coin_name, (_, channel_url) in config.channels.items()
            ])
        ),
        disable_web_page_preview = True
    )


@dispatcher.startup()
async def on_startup() -> None:
    scheduler: AsyncIOScheduler = AsyncIOScheduler(
        timezone = utc_timezone
    )

    for minute in range(0, 60):
        scheduler.add_job(
            func = exchange_checker,
            trigger = CronTrigger(
                minute = minute
            )
        )

    scheduler.start()

    try:
        await bot.edit_message_text(
            chat_id = config.main_channel_id,
            message_id = config.main_channel_message_id,
            text = TEXTS.channels_list.format(
                channels = "\n".join([
                    TEXTS.channel.format(
                        coin_name = coin_name,
                        channel_url = channel_url
                    )
                    for coin_name, (_, channel_url) in config.channels.items()
                ])
            )
        )

    except exceptions.TelegramAPIError:
        pass


@dispatcher.shutdown()
async def on_shutdown() -> None:
    pass


if __name__ == "__main__":
    dispatcher.run_polling(bot)
