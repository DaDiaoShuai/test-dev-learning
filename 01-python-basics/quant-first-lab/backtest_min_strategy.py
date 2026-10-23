"""量化加餐 2 · 用历史数据回测第一课的最小策略（EMA 金叉买、死叉/止损卖 + RSI 过滤）。

纯学习用途，输出不构成买卖建议。只做历史回测：不下单、不连账户、不碰合约杠杆。
数据来自币安公开行情接口（data-api.binance.vision），免费、免 key。
依赖只有 requests，和 quant_first_lab.py 在同一个目录、同一套跑法。
"""

import statistics
from datetime import datetime

import requests

API = "https://data-api.binance.vision/api/v3/klines"
SYMBOL = "BTCUSDT"        # 只回测现货 BTC
INTERVAL = "1h"           # 1 小时 K 线
TOTAL_BARS = 3000         # 约 125 天历史（接口单次最多 1000 根，下面自动翻页）
FEE = 0.001               # 单边手续费 0.1%（币安现货大致水平），买卖各扣一次
START_CASH = 10_000.0     # 假设起始资金 10000 USDT，方便算百分比


# ---------- 取数据 ----------

def get_klines(total):
    """拉够 total 根 K 线，返回 (开盘时间列表, 开盘价列表, 收盘价列表)。

    接口默认返回最近 1000 根；要更早的数据，用 endTime 往回翻页再拼起来。
    """
    pages, end, got = [], None, 0
    while got < total:
        params = {"symbol": SYMBOL, "interval": INTERVAL, "limit": 1000}
        if end is not None:
            params["endTime"] = end
        resp = requests.get(API, params=params, timeout=15)
        resp.raise_for_status()
        rows = resp.json()
        if not rows:
            break
        pages.append(rows)
        got += len(rows)
        end = rows[0][0] - 1            # 下一页取这页第一根之前的
    all_rows = [r for page in reversed(pages) for r in page][-total:]
    times = [r[0] for r in all_rows]               # K 线开盘时间（毫秒时间戳）
    opens = [float(r[1]) for r in all_rows]         # 开盘价
    closes = [float(r[4]) for r in all_rows]        # 收盘价
    return times, opens, closes


# ---------- 指标（和第一课脚本同一套算法，这次算整条序列） ----------

def ema_series(values, n):
    """指数移动平均序列：越新的价格权重越大。"""
    k = 2 / (n + 1)
    out = [values[0]]
    for v in values[1:]:
        out.append(out[-1] + k * (v - out[-1]))
    return out


def rsi_series(values, n=14):
    """Wilder 版 RSI 序列：前 n 根还没有值，用 None 占位。"""
    out = [None] * len(values)
    changes = [values[i] - values[i - 1] for i in range(1, len(values))]
    if len(changes) <= n:
        return out
    avg_gain = sum(max(c, 0) for c in changes[:n]) / n
    avg_loss = sum(max(-c, 0) for c in changes[:n]) / n
    for i in range(n, len(changes)):
        gain = max(changes[i], 0)
        loss = max(-changes[i], 0)
        avg_gain = (avg_gain * (n - 1) + gain) / n
        avg_loss = (avg_loss * (n - 1) + loss) / n
        rs = avg_gain / avg_loss if avg_loss > 0 else float("inf")
        out[i + 1] = 100 - 100 / (1 + rs)
    return out


# ---------- 回测核心 ----------

def run_backtest(opens, closes, fast=10, slow=30, rsi_max=70, stop_pct=0.04):
    """跑一遍策略，返回一组成绩（字典）。

    规则 = 第一课最小策略：
      买入：EMA(fast) 上穿 EMA(slow)（金叉），且 RSI < rsi_max（不追超买）
      卖出：EMA(fast) 下穿 EMA(slow)（死叉），或价格较买入价跌 stop_pct（止损）
    防未来函数：信号在收盘后产生，统一在下一根 K 线的开盘价成交。
    全仓进、全仓出，只做现货多头（有币就持有，没币就等信号）。
    """
    e_fast = ema_series(closes, fast)
    e_slow = ema_series(closes, slow)
    rsi = rsi_series(closes, 14)

    cash = START_CASH
    coin = 0.0
    entry_price = None   # 买入成交价（止损按它算）
    entry_cash = None    # 买入前手里的现金（算单笔盈亏用）
    pending = None       # 待执行信号："buy" / "sell"，下一根开盘执行
    trades = []          # 每笔已平仓交易的收益率（已扣双边手续费）
    equity = []          # 每根 K 线收盘时的总资产曲线（算回撤和夏普用）

    for i in range(len(closes)):
        # 1）先执行上一根收盘产生的信号（在本根开盘价成交）
        if pending == "buy" and coin == 0:
            entry_cash = cash
            entry_price = opens[i]
            coin = cash * (1 - FEE) / opens[i]
            cash = 0.0
        elif pending == "sell" and coin > 0:
            cash = coin * opens[i] * (1 - FEE)
            trades.append(cash / entry_cash - 1)
            coin = 0.0
            entry_price = None
        pending = None

        # 2）记录这根收盘时的总资产
        equity.append(cash + coin * closes[i])

        # 3）指标没算热之前（慢线周期 + RSI）不产生信号
        if i < slow + 1 or rsi[i] is None:
            continue

        # 4）产生信号
        golden = e_fast[i - 1] <= e_slow[i - 1] and e_fast[i] > e_slow[i]
        death = e_fast[i - 1] >= e_slow[i - 1] and e_fast[i] < e_slow[i]
        if coin == 0 and golden and rsi[i] < rsi_max:
            pending = "buy"
        elif coin > 0 and (death or closes[i] <= entry_price * (1 - stop_pct)):
            pending = "sell"

    # 回测结束还拿着币：按最后一根收盘价"平仓"，这笔也计入成绩
    if coin > 0:
        cash = coin * closes[-1] * (1 - FEE)
        trades.append(cash / entry_cash - 1)
        equity[-1] = cash

    # ---------- 把成绩算出来 ----------
    wins = [t for t in trades if t > 0]
    losses = [t for t in trades if t <= 0]
    win_rate = len(wins) / len(trades) if trades else 0.0
    if wins and losses:
        profit_loss = (sum(wins) / len(wins)) / abs(sum(losses) / len(losses))
    else:
        profit_loss = float("nan")  # 全赢或全输时盈亏比没意义，输出里会标 n/a

    # 夏普：用每小时资产收益率的均值/标准差，年化（一年 24*365 小时），越高越"稳地赚"
    rets = [equity[i] / equity[i - 1] - 1 for i in range(1, len(equity))]
    sd = statistics.stdev(rets) if len(rets) > 1 else 0.0
    sharpe = (statistics.mean(rets) / sd * (24 * 365) ** 0.5) if sd > 0 else 0.0

    # 最大回撤：资产从最高点跌到随后最低点的最大幅度
    peak, max_dd = equity[0], 0.0
    for v in equity:
        peak = max(peak, v)
        max_dd = max(max_dd, (peak - v) / peak)

    return {
        "total_return": cash / START_CASH - 1,
        "trades": len(trades),
        "win_rate": win_rate,
        "profit_loss": profit_loss,
        "sharpe": sharpe,
        "max_drawdown": max_dd,
    }


def pct(x):
    return f"{x * 100:+.1f}%" if x == x else "n/a"  # x==x 用来挡 nan


# ---------- 跑起来 ----------

def main():
    times, opens, closes = get_klines(TOTAL_BARS)
    t0 = datetime.fromtimestamp(times[0] / 1000).strftime("%Y-%m-%d")
    t1 = datetime.fromtimestamp(times[-1] / 1000).strftime("%Y-%m-%d")
    print(f"数据：{SYMBOL} {INTERVAL} K 线 {len(closes)} 根（{t0} 至 {t1}），现货历史行情")
    print(f"假设：起始 {START_CASH:,.0f} USDT，全仓进出，单边手续费 {FEE * 100:.1f}%")
    print("（纯学习回测，不构成买卖建议）\n")

    base = run_backtest(opens, closes)  # 默认参数 EMA10/30 + RSI<70 + 4% 止损
    buy_hold = closes[-1] / closes[0] - 1
    print("=== 基准参数 EMA10/30 ===")
    print(f"总收益：{pct(base['total_return'])}   （同期买入不动：{pct(buy_hold)}）")
    print(f"交易次数：{base['trades']} 笔已平仓")
    print(f"胜率：{base['win_rate'] * 100:.1f}%  （赚钱的笔数 ÷ 总笔数）")
    pl = base["profit_loss"]
    print(f"盈亏比：{pl:.2f}" if pl == pl else "盈亏比：n/a（没有亏损或没有盈利交易）",
          " （平均每笔盈利 ÷ 平均每笔亏损）")
    print(f"夏普比率：{base['sharpe']:.2f}   （>1 还行，>2 很好；越高表示赚得越稳）")
    print(f"最大回撤：{base['max_drawdown'] * 100:.1f}%   （资产从最高点最多跌回去多少，>20% 很难拿得住）")

    print("\n=== 参数敏感性：参数稍微改一改，成绩变成什么样 ===")
    variants = [(10, 30), (8, 28), (12, 36), (5, 20), (20, 60)]
    results = {}
    for fast, slow in variants:
        r = run_backtest(opens, closes, fast, slow)
        results[(fast, slow)] = r
        pl = r["profit_loss"]
        pl_s = f"{pl:.2f}" if pl == pl else "n/a"
        print(f"EMA{fast}/{slow}：总收益 {pct(r['total_return'])}，{r['trades']} 笔，"
              f"胜率 {r['win_rate'] * 100:.0f}%，盈亏比 {pl_s}，最大回撤 {r['max_drawdown'] * 100:.1f}%")

    # 用 ±20% 的小改动（8/28、12/36 对比 10/30）判断稳不稳健
    near = [results[k]["total_return"] for k in [(8, 28), (10, 30), (12, 36)]]
    spread = max(near) - min(near)
    same_sign = all(x > 0 for x in near) or all(x < 0 for x in near)
    print("\n=== 结论 ===")
    if not same_sign or spread >= 0.30:
        print(f"参数只小改 ±20%，总收益就从 {pct(max(near))} 掉到 {pct(min(near))}，"
              f"摆动 {spread * 100:.0f} 个百分点 → 默认参数跑出的这点成绩没有余量，"
              "稍微一动就归零甚至转亏。对参数这么敏感的结果不能当成策略有效，"
              "这正是过拟合的风险长相。实盘前先回测，说的就是这一步。")
    elif all(x < 0 for x in near):
        print("参数小改大改都是亏的，还跑输同期买入不动 → 这次不是过拟合的问题，"
              "是策略本身在这段行情里就没有优势：参数不敏感地不赚钱，同样不能上实盘。")
    else:
        print("参数小改（±20%）后成绩方向一致、差距不大 → 在这段历史里相对稳健，"
              "但这只是样本内结论，换段时间仍要重新验证。")


if __name__ == "__main__":
    main()
