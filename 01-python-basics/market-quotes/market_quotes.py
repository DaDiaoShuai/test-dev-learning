# market_quotes.py — 真实行情抓取（骨架版，你来补 TODO 1~3）
#
# 练的还是第 1 周那几样：requests 发请求、从字典里取字段、f-string 拼字符串。
# 对照 JS 想：Python 的 data["price"] 就相当于 JS 的 data.price / data["price"]，
# float("123.45") 相当于 JS 的 Number("123.45")，None 相当于 JS 的 null。

import requests

# 有些接口会拒绝默认的请求标识，统一带一个浏览器标识，这个直接用，不用改。
HEADERS = {"User-Agent": "Mozilla/5.0"}


def get_json(url):
    """已经写好的工具函数（P5 的升级版）：发 GET 请求，把返回的 JSON 变成字典。

    JS 对照：相当于 fetch(url).then(r => r.json())，只是这里是同步的，不用 await。
    """
    response = requests.get(url, headers=HEADERS, timeout=10)
    if response.status_code != 200:
        raise Exception(f"请求失败，状态码 {response.status_code}，地址：{url}")
    return response.json()


# TODO 1：抓加密货币价格（BTC / ETH）
# 数据源：币安公开行情（免 key），symbol 例："BTCUSDT"、"ETHUSDT"
# 请求地址拼法：f"https://data-api.binance.vision/api/v3/ticker/price?symbol={symbol}"
# 返回长这样：{"symbol": "BTCUSDT", "price": "82291.58"}
# 价格在 "price" 字段里，是字符串，要用 float() 转成数字再 return。
# 如果这个地址在你的网络下打不开，备选：Coinbase 的
# f"https://api.coinbase.com/v2/prices/{symbol}-USD/spot"（symbol 传 "BTC"），
# 价格在 data["data"]["amount"] 里，取法套路一样。
def get_crypto_price(symbol):
    # 你来补：拼 url -> get_json(url) -> 取字段 -> float() -> return
    url = f"https://data-api.binance.vision/api/v3/ticker/price?symbol={symbol}"
    data = get_json(url)
    price = float(data["price"])
    return price


# TODO 2：抓现货黄金价格（美元/盎司）
# 数据源：gold-api 公开行情（免 key）
# 请求地址：https://api.gold-api.com/price/XAU
# 返回长这样：{"symbol": "XAU", "price": 4091.6, "currency": "USD", ...}
# 价格在 "price" 字段里，本身就是数字，float() 转一下再 return。
def get_gold_price():
    # 你来补：get_json(地址) -> 取 "price" -> float() -> return
    url = "https://api.gold-api.com/price/XAU"
    data = get_json(url)
    price = float(data["price"])
    return price


# TODO 3：抓期货价格（布伦特 BZ=F / WTI CL=F）
# 数据源：Yahoo Finance 行情（免 key），symbol 例："BZ=F"（布伦特）、"CL=F"（WTI）
# 请求地址拼法：f"https://query2.finance.yahoo.com/v8/finance/chart/{symbol}"
# 返回是层层嵌套的字典+列表，价格藏在：
# data["chart"]["result"][0]["meta"]["regularMarketPrice"]
# JS 对照：就是 data.chart.result[0].meta.regularMarketPrice，把点换成下标而已。
# 一层一层取，取到后 float() 转成数字再 return。
def get_yahoo_price(symbol):
    # 你来补：拼 url -> get_json(url) -> 一层层取到 regularMarketPrice -> float() -> return
    url = f"https://query2.finance.yahoo.com/v8/finance/chart/{symbol}"
    data = get_json(url)
    price = float(data["chart"]["result"][0]["meta"]["regularMarketPrice"])
    return price


def get_all_quotes():
    """已经写好：汇总 5 个品种，返回一个字典。

    等你把 TODO 1~3 补完，这个函数自然就能用了。
    """
    return {
        "BTC": get_crypto_price("BTCUSDT"),
        "ETH": get_crypto_price("ETHUSDT"),
        "黄金": get_gold_price(),
        "布伦特": get_yahoo_price("BZ=F"),
        "WTI": get_yahoo_price("CL=F"),
    }


def format_quote(name, price):
    """已经写好：f-string 把一行行情拼成可读字符串（P2 的实战）。"""
    if price is None:
        return f"{name}：没抓到"
    return f"{name}：{price:,.2f} 美元"


if __name__ == "__main__":
    quotes = get_all_quotes()
    for name, price in quotes.items():
        print(format_quote(name, price))
