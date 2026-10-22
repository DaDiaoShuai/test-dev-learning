# 真实行情抓取练习（第 1 周 · requests 实战）

把 P5 的 requests 练习换成真家伙：抓你每天晨间简报里都在看的 5 个品种的真实价格，写代码取数，再用 pytest 一跑就知道对不对。不再对着示例网站的假数据练。

只用第 1 周已经练过的东西：requests 发请求、字典取字段、f-string 拼字符串。不引入新概念。

## 要抓的 5 个品种

| 品种 | 数据源（免费、免 key） | 价格在返回的哪里 |
| --- | --- | --- |
| BTC | 币安公开行情 `data-api.binance.vision` | `data["price"]`，字符串 |
| ETH | 币安公开行情 `data-api.binance.vision` | `data["price"]`，字符串 |
| 现货黄金 | gold-api `api.gold-api.com/price/XAU` | `data["price"]`，数字 |
| 布伦特原油 | Yahoo Finance `BZ=F` | `data["chart"]["result"][0]["meta"]["regularMarketPrice"]` |
| WTI 原油 | Yahoo Finance `CL=F` | 同上 |

数据源全部免费且不需要 API key，仓库里不存放任何 key 和个人信息。

## 你要补的只有 3 处

打开 `market_quotes.py`，补完 TODO 1~3，每个函数就三四行：

1. `get_crypto_price(symbol)` — 拼地址 → `get_json()` → 取 `"price"` → `float()` 返回
2. `get_gold_price()` — `get_json()` → 取 `"price"` → `float()` 返回
3. `get_yahoo_price(symbol)` — 拼地址 → `get_json()` → 一层层取到 `regularMarketPrice` → `float()` 返回

其余代码（发请求的 `get_json`、汇总字典、打印）都写好了。每个 TODO 上方都有返回数据的样子和 JS 对照提示，照着取就行。

JS 对照速记：

- `data["price"]` ≈ JS 的 `data.price`
- `float("82291.58")` ≈ JS 的 `Number("82291.58")`
- `None` ≈ JS 的 `null`
- 字典里套列表再套字典，取法和 JS 里把 `.` 换成下标完全对应

## 怎么跑

```bash
cd 01-python-basics/market-quotes
pip install -r requirements.txt   # 装过 requests 和 pytest 就跳过
python market_quotes.py           # 先看能不能打印出 5 行真实价格
pytest -v                         # 再跑断言验收
```

## 验收：断言和任务一一对应

`test_market_quotes.py` 已写好、不用改，6 条断言：

| 断言 | 检查什么 |
| --- | --- |
| `test_btc_price` | BTC 抓到了、是 float、是正数 |
| `test_eth_price` | ETH 同上 |
| `test_gold_price` | 黄金同上 |
| `test_brent_price` | 布伦特同上（嵌套字段取对了） |
| `test_wti_price` | WTI 同上 |
| `test_all_quotes_has_five_symbols` | 汇总字典正好 5 个品种，且没有一个是 None |

补完之前跑是红的属正常，失败信息会直说哪个字段没取到；3 处 TODO 补对，6 条全绿。再补一条自检：把打印出来的价格和你当天晨间简报里的数字对一眼，量级对得上就算真通了。

## 网络备选

如果币安那个地址在你的网络下打不开，把 TODO 1 换成骨架注释里写的 Coinbase 备选地址，取法套路一样；其余品种不受影响。某个品种偶发请求失败，先重跑一次再下结论。
