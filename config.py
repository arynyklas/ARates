from pathlib import Path
from pydantic import BaseModel
from yaml import dump as yaml_dump, load as yaml_load, Loader as YAMLLoader

from typing import List, Dict, Tuple


CONFIG_FILEPATH: Path = Path(__file__).parent / "config.yml"


class CoingeckoConfig(BaseModel):
    prices_checker_delay: int
    vs_currency: str
    chart_days: int


class Config(BaseModel):
    bot_token: str
    logs_chat_id: int
    logger_name: str
    logger_level: str
    main_channel_id: int
    main_channel_url: str
    main_channel_title: str
    main_channel_message_id: int
    coingecko: CoingeckoConfig
    upload_filename: str
    proxies: List[str]
    coins: Dict[str, str]
    channels: Dict[str, Tuple[int, str]]
    parse_prices: Dict[str, Tuple[str, int]]

    def save(self) -> None:
        with CONFIG_FILEPATH.open("w", encoding="utf-8") as file:
            yaml_dump(
                data = self.dict(),
                stream = file,
                indent = 2,
                allow_unicode = True,
                encoding = "utf-8",
                sort_keys = False
            )


with CONFIG_FILEPATH.open("r", encoding="utf-8") as file:
    config_data: dict = yaml_load(
        stream = file,
        Loader = YAMLLoader
    )


config: Config = Config.parse_obj(
    obj = config_data
)
