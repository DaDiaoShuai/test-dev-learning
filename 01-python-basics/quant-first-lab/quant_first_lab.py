# 量化第一课 · 动手小实验：给 BTC 做一次"行情判型"
# 只用今晚 Python 课练的技能：requests 发请求、字典取字段、f-string 打印
# 跑法：python quant_first_lab.py   （需先 pip install requests）
import requests

def get_klines(symbol="BTCUSDT", interval="1h", limit=200):
    # 币安公开行情接口，不用 key；api.binance.com 在部分地区受限，这里用 vision 镜像
    url = "https://data-api.binance.vision/api/v3/klines"
    r = requests.get(url, params={"symbol": symbol, "interval": interval, "limit": limit}, timeout=15)
    r.raise_for_status()
    return [float(k[4]) for k in r.json()]  # 每根 K 线取收盘价

def ema(vals, n):
    k = 2 / (n + 1)
    e = vals[0]
    out = []
    for v in vals:
        e = v * k + e * (1 - k)
        out.append(e)
    return out

def rsi(vals, n=14):
    gains, losses = [], []
    for i in range(1, len(vals)):
        ch = vals[i] - vals[i - 1]
        gains.append(max(ch, 0)); losses.append(max(-ch, 0))
    ag = sum(gains[:n]) / n; al = sum(losses[:n]) / n
    for i in range(n, len(gains)):
        ag = (ag * (n - 1) + gains[i]) / n
        al = (al * (n - 1) + losses[i]) / n
    return 100 - 100 / (1 + ag / al) if al else 100.0

closes = get_klines()
now = closes[-1]
e10, e30 = ema(closes, 10)[-1], ema(closes, 30)[-1]
# 死叉/金叉是第几根 K 线前形成的
golden = ema(closes, 10)[-1] > ema(closes, 30)[-1]
bars = 0
e10s, e30s = ema(closes, 10), ema(closes, 30)
for i in range(len(closes) - 1, 0, -1):
    if (e10s[i] > e30s[i]) != golden: break
    bars += 1
r = rsi(closes)
ma20 = sum(closes[-20:]) / 20
sd = (sum((c - ma20) ** 2 for c in closes[-20:]) / 20) ** 0.5
upper, lower = ma20 + 2 * sd, ma20 - 2 * sd
pos = (now - lower) / (upper - lower) * 100

print(f"BTC 现价: {now:,.1f} USDT")
print(f"EMA10 {e10:,.1f} / EMA30 {e30:,.1f} → {'金叉' if golden else '死叉'}（约{bars}小时前形成）")
print(f"RSI14: {r:.1f} → {'超卖(<30)' if r < 30 else '超买(>70)' if r > 70 else '中性区'}")
print(f"布林带(20,2): 下轨 {lower:,.1f} / 中轨 {ma20:,.1f} / 上轨 {upper:,.1f}，价格在带内 {pos:.0f}% 位置")
print("---- 判型小抄（学习用，不是买卖建议）----")
print("· 趋势跟踪：看均线死叉/金叉，震荡市里会被反复打脸")
print("· 均值回归：RSI<30 且贴下轨 = 按规则'跌过头'区，但真趋势里这是接飞刀")
print("· 网格交易：先看近 7 天最高最低，区间没破才有得玩")
print("· 突破/动量：等价格带量冲出区间再说，现在不是它的菜")
