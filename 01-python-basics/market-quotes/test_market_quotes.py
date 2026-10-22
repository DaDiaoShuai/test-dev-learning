# test_market_quotes.py — 行情抓取的断言（已写好，不用改）
#
# 和任务说明里的验收表一一对应：每个品种一条，另加一条汇总检查。
# 运行方式：在本目录下执行 pytest -v
# 补完骨架之前跑是红的，而且每条失败信息都会直说缺什么；
# 把 market_quotes.py 的 TODO 1~3 补对，这里会全部变绿。
#
# 写法就是最朴素的 assert：assert 条件, "失败时给人看的话"
# 相当于 JS 里测试的 expect(...).toBe(...) 那种断言，只是这里条件自己写。

from market_quotes import get_all_quotes, get_crypto_price, get_gold_price, get_yahoo_price


def test_btc_price():
    price = get_crypto_price("BTCUSDT")
    assert price is not None, "BTC 价格是 None：get_crypto_price 还没补完，或返回里没取到 price 字段"
    assert isinstance(price, float), f"BTC 价格应该是 float，却是 {type(price)}：记得用 float() 转"
    assert price > 0, f"BTC 价格应该是正数，却是 {price}"


def test_eth_price():
    price = get_crypto_price("ETHUSDT")
    assert price is not None, "ETH 价格是 None：get_crypto_price 还没补完，或返回里没取到 price 字段"
    assert isinstance(price, float), f"ETH 价格应该是 float，却是 {type(price)}：记得用 float() 转"
    assert price > 0, f"ETH 价格应该是正数，却是 {price}"


def test_gold_price():
    price = get_gold_price()
    assert price is not None, "黄金价格是 None：get_gold_price 还没补完，或返回里没取到 price 字段"
    assert isinstance(price, float), f"黄金价格应该是 float，却是 {type(price)}：记得用 float() 转"
    assert price > 0, f"黄金价格应该是正数，却是 {price}"


def test_brent_price():
    price = get_yahoo_price("BZ=F")
    assert price is not None, "布伦特价格是 None：get_yahoo_price 还没补完，或嵌套字段没取到 regularMarketPrice"
    assert isinstance(price, float), f"布伦特价格应该是 float，却是 {type(price)}：记得用 float() 转"
    assert price > 0, f"布伦特价格应该是正数，却是 {price}"


def test_wti_price():
    price = get_yahoo_price("CL=F")
    assert price is not None, "WTI 价格是 None：get_yahoo_price 还没补完，或嵌套字段没取到 regularMarketPrice"
    assert isinstance(price, float), f"WTI 价格应该是 float，却是 {type(price)}：记得用 float() 转"
    assert price > 0, f"WTI 价格应该是正数，却是 {price}"


def test_all_quotes_has_five_symbols():
    quotes = get_all_quotes()
    expected = {"BTC", "ETH", "黄金", "布伦特", "WTI"}
    assert set(quotes.keys()) == expected, f"品种不对：应该是 {expected}，实际是 {set(quotes.keys())}"
    missing = [name for name, price in quotes.items() if price is None]
    assert not missing, f"这几个品种没抓到价格：{missing}，看上面对应的那条失败信息"
