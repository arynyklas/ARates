from httpx import AsyncClient, HTTPError
from json import JSONDecodeError
from datetime import datetime
from matplotlib import pyplot, dates as matplotlib_dates
from pandas import DataFrame
from io import BytesIO
from pytz import utc as utc_timezone

import seaborn

from typing import Optional, List, Tuple


class HTTPMethods:
    GET: str = "GET"


class CoinGecko:
    BASE_URL: str = "https://api.coingecko.com/api/v3/coins/{coin}{method}"
    TIMEOUT: float = 3.0

    def __init__(self, vs_currency: str, chart_days: int, proxies: Optional[List[str]]=None) -> None:
        self.vs_currency: str = vs_currency
        self.chart_days: int = chart_days

        if not proxies:
            proxies = [
                None
            ]

        self._http_clients: List[AsyncClient] = [
            AsyncClient(
                proxies = proxy,
                timeout = self.TIMEOUT,
                verify = False
            )
            for proxy in proxies
        ]

        self._http_clients_count: int = len(self._http_clients)

        self._http_clients_index: int = 0

    @property
    def _http_client(self) -> AsyncClient:
        if self._http_clients_index == len(self._http_clients):
            self._http_clients_index = 0

        http_client: AsyncClient = self._http_clients[self._http_clients_index]

        self._http_clients_index += 1

        return http_client

    async def _request(self, coin: str, method: str, http_method: str, retries: Optional[int]=0, **request_kwargs) -> dict:
        url: str = self.BASE_URL.format(
            coin = coin,
            method = method
        )

        while True:
            try:
                return (
                    await self._http_client.request(
                        method = http_method,
                        url = url,
                        **request_kwargs
                    )
                ).json()

            except (HTTPError, JSONDecodeError) as ex:
                retries += 1

                if retries == self._http_clients_count:
                    raise ex

    async def get_market_data(self, coin_code: str) -> dict:
        return (
            await self._request(
                coin = coin_code,
                method = "",
                http_method = HTTPMethods.GET
            )
        )["market_data"]

    async def get_market_chart(self, coin_code: str) -> List[List[float]]:
        return (
            await self._request(
                coin = coin_code,
                method = "/market_chart",
                http_method = HTTPMethods.GET,
                params = dict(
                    vs_currency = self.vs_currency,
                    days = self.chart_days
                )
            )
        )["prices"]

    async def create_plot(self, coin_code: str, title: Optional[str]=None) -> BytesIO:
        market_chart_data: List[Tuple[float, float]] = await self.get_market_chart(
            coin_code = coin_code
        )

        times: List[datetime] = []
        prices: List[float] = []

        for timestamp_ms, price in market_chart_data:
            times.append(
                datetime.fromtimestamp(
                    timestamp_ms // 1000,
                    tz = utc_timezone
                )
            )

            prices.append(
                round(price, 6)
            )

        seaborn.set_theme()

        pyplot.figure(
            figsize = (12, 6)
        )

        ax: pyplot.Axes = seaborn.lineplot(
            x = "Time",
            y = "Price",
            data = DataFrame(
                data = {
                    "Time": times,
                    "Price": prices
                }
            )
        )

        ax.set_xlabel("")
        ax.set_ylabel("")

        if title:
            pyplot.title(
                label = title,
                loc = "center",
                pad = 12
            )

        ax.xaxis.set_major_formatter(
            formatter = matplotlib_dates.DateFormatter(
                fmt = "%H:%M",
                tz = utc_timezone
            )
        )

        ax.xaxis.set_major_locator(
            locator = matplotlib_dates.HourLocator(
                interval = 1
            )
        )

        pyplot.xticks(
            rotation = 45,
            ha = "right"
        )

        pyplot.tight_layout()

        buffered_file: BytesIO = BytesIO()

        pyplot.savefig(
            buffered_file,
            format = "png"
        )

        pyplot.close()

        buffered_file.seek(0)

        return buffered_file
