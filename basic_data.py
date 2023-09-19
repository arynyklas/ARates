class TEXTS:
    default_message: str = "We update coins' prices every minute.\n\nOur channels:\n{channels}\n\n• <a href=\"{main_channel_url}\">{main_channel_title}</a>"
    channel: str = "{coin_name} — <a href=\"{channel_url}\">link</a> — {channel_price}"
    channel_price: str = "<b>{currency_price} {vs_currency}</b>"
    channel_notify: str = "{prices}\n\n• <a href=\"https://www.coingecko.com/en/coins/{coin_code}\">CoinGecko.com</a>\n\n• <a href=\"{main_channel_url}\">{main_channel_title}</a>\n\n{date} {time}"
    price: str = "• {currency_name} <b>{currency_price}</b> <i>{currency_persentage}%</i>"
