from httpx import AsyncClient, ReadTimeout

from matplotlib import pyplot, dates as matplotlib_dates
from datetime import datetime
from io import BytesIO

from pytz import utc as utc_timezone

from typing import Optional, List, Union, Tuple


class CoinGecko:
    BASE_URL: str = "https://api.coingecko.com/api/v3/coins/{coin}{method}"
    TIMEOUT: float = 3.0

    def __init__(self, vs_currency: str, chart_days: int, proxies: Optional[List[Union[str, None]]]=None) -> None:
        self.vs_currency: str = vs_currency
        self.chart_days: int = chart_days

        if not proxies:
            proxies = [
                None
            ]

        self._http_clients: List[AsyncClient] = [
            AsyncClient(
                proxies = proxy,
                timeout = self.TIMEOUT
            )
            for proxy in proxies
        ]

        self._http_clients_index: int = 0

    @property
    def _http_client(self) -> AsyncClient:
        if self._http_clients_index == len(self._http_clients):
            self._http_clients_index = 0

        http_client: AsyncClient = self._http_clients[self._http_clients_index]

        self._http_clients_index += 1

        return http_client

    async def _request(
        self,
        coin: str,
        method: Optional[str]=None,
        http_method: Optional[str]=None,
        **kwargs
    ) -> dict:
        while True:
            try:
                return (
                    await self._http_client.request(
                        method = http_method or "GET",
                        url = self.BASE_URL.format(
                            coin = coin,
                            method = (
                                method
                                if method
                                else
                                ""
                            )
                        ),
                        **kwargs
                    )
                ).json()

            except ReadTimeout:
                pass

    async def get_market_data(self, coin_code: str) -> dict:
        return (
            await self._request(
                coin = coin_code
            )
        )["market_data"]

    async def get_market_chart(self, coin_code: str) -> List[List[float]]:
        return (
            await self._request(
                coin = coin_code,
                method = "/market_chart",
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

            prices.append(round(price, 2))

        _, ax = pyplot.subplots()

        if title:
            pyplot.title(
                label = title,
                loc = "center",
                pad = 16
            )

        pyplot.plot(times, prices)

        ax.xaxis.set_major_formatter(
            formatter = matplotlib_dates.DateFormatter(
                fmt = "%H:%M",
                tz = utc_timezone
            )
        )

        file: BytesIO = BytesIO()

        pyplot.savefig(
            file,
            format = "png"
        )

        pyplot.close()

        file.seek(0)

        return file
