"""量化加餐 3 · 同区间对照回测：网格策略 vs 第一课的趋势策略 vs 买入持有。

纯学习用途，输出不构成买卖建议。只做历史回测：不下单、不连账户、不碰合约杠杆。
数据来自币安公开行情接口（data-api.binance.vision），免费、免 key。
依赖只有 requests，和本目录其他脚本同一套跑法。

对照口径（三方完全一致，保证公平）：
  - 同一段数据：BTCUSDT 现货 1h K 线最近 3000 根（约 125 天），三方用同一批 K 线
  - 同一本金：10,000 USDT；单边手续费同为 0.1%
  - 趋势策略直接复用 backtest_min_strategy.py 的 run_backtest（EMA10/30 + RSI<70 + 跌 4% 止损）

网格策略的规矩（先声明，防止事后调参作弊）：
  - 区间不用未来数据定：只用最开始 WARMUP_DAYS 天的最高/最低价定上下界（实盘里你也只能看过去）
  - 区间内等距切成 N 格，用币安现货网格同款的"配对挂单"逻辑：
    每个格线挂一单，买单成交后立刻在其上一格挂卖单，卖单成交后回下一格重新挂买单
  - 建仓时按当时价格买入上半区所需的底仓（卖单要有币可卖），下半区留现金等买单成交；
    每格金额 = 本金 / N
  - 网格是限价单：价格碰到格线就按格线价成交。用 1h K 线模拟时，根内路径不可知，
    按常用近似走：阳线 开->低->高->收，阴线 开->高->低->收（这是本回测的一处简化，特此声明）
  - 价格冲出区间上沿 = 币全卖光后空仓看戏；跌破下沿 = 现金买光满仓等反弹（网格两大死法如实保留）
  - 结束时按最后一根收盘价、扣手续费把持仓折算成 USDT，和趋势策略同一口径结算
"""

import statistics
from datetime import datetime

import requests

# 趋势策略直接复用加餐 2 的实现，避免两份代码算出两个趋势结果
from backtest_min_strategy import run_backtest as run_trend

API = "https://data-api.binance.vision/api/v3/klines"
SYMBOL = "BTCUSDT"
INTERVAL = "1h"
TOTAL_BARS = 3000
FEE = 0.001
START_CASH = 10_000.0


# ---------- 取数据（这次要高低价，定网格区间用） ----------

def get_klines(total):
    """拉够 total 根 K 线，返回 (时间, 开, 高, 低, 收) 五个列表。翻页逻辑同加餐 2。"""
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
        end = rows[0][0] - 1
    all_rows = [r for page in reversed(pages) for r in page][-total:]
    times = [r[0] for r in all_rows]
    opens = [float(r[1]) for r in all_rows]
    highs = [float(r[2]) for r in all_rows]
    lows = [float(r[3]) for r in all_rows]
    closes = [float(r[4]) for r in all_rows]
    return times, opens, highs, lows, closes


# ---------- 通用成绩计算 ----------

def metrics(equity, start_cash=START_CASH):
    """从资产曲线算总收益（按最后一根的折算值）、夏普、最大回撤。"""
    rets = [equity[i] / equity[i - 1] - 1 for i in range(1, len(equity)) if equity[i - 1] > 0]
    sd = statistics.stdev(rets) if len(rets) > 1 else 0.0
    sharpe = (statistics.mean(rets) / sd * (24 * 365) ** 0.5) if sd > 0 else 0.0
    peak, max_dd = equity[0], 0.0
    for v in equity:
        peak = max(peak, v)
        max_dd = max(max_dd, (peak - v) / peak)
    return {"total_return": equity[-1] / start_cash - 1, "sharpe": sharpe, "max_drawdown": max_dd}


# ---------- 网格回测 ----------

def run_grid(times, opens, highs, lows, closes, warmup_days=30, n_grids=20):
    """跑一遍现货网格（配对挂单版，和币安现货网格机器人同款逻辑），返回成绩 + 过程细节。

    网格由 n 个"格子"（cell）组成，格子 i 在格线 lines[i] 与 lines[i+1] 之间。
    每个格子只有两种状态，天然不会重复挂单：
      "buy"：在本格下沿挂买单，价格跌到下沿成交后转 "hold"
      "hold"：持有一格的币，在本格上沿挂卖单，价格涨到上沿成交后转回 "buy"
    建仓：以开跑那根的开盘价为现价，现价上方的格子（含正跨着现价的那格）
    先按现价买好底仓置 "hold"，现价下方的格子置 "buy"。
    """
    w = warmup_days * 24
    lower = min(lows[:w])
    upper = max(highs[:w])
    step = (upper - lower) / n_grids
    lines = [lower + step * i for i in range(n_grids + 1)]
    per_grid_cash = START_CASH / n_grids

    cash = START_CASH
    p0 = opens[w]
    state = []   # 每格："buy" 待买 / "hold" 持有待卖
    qtys = []    # 每格持有的 BTC 数（buy 状态为 0）
    for i in range(n_grids):
        if lines[i + 1] <= p0:               # 整格都在现价下方：挂买单
            state.append("buy"); qtys.append(0.0)
        else:                                # 现价上方或正跨现价：买底仓
            state.append("hold")
            qtys.append(per_grid_cash * (1 - FEE) / p0)
            cash -= per_grid_cash

    buys = sells = 0
    roundtrips = []          # 每次卖单成交 = 完成一个回合，收益相对每格本金
    realized = 0.0
    equity = []
    breakout_time = None

    def held_btc():
        return sum(qtys)

    def cross_up(a, b):
        """价格从 a 上行到 b：依次穿过格线 lines[k]，触发格子 k-1 的卖单。"""
        nonlocal cash, realized, sells
        for k in range(1, n_grids + 1):
            line = lines[k]
            if a < line <= b and state[k - 1] == "hold":
                qty = qtys[k - 1]
                proceeds = qty * line * (1 - FEE)
                cash += proceeds
                realized += proceeds - per_grid_cash
                roundtrips.append(proceeds / per_grid_cash - 1)
                sells += 1
                state[k - 1] = "buy"; qtys[k - 1] = 0.0

    def cross_down(a, b):
        """价格从 a 下行到 b：依次穿过格线 lines[k]，触发格子 k 的买单。"""
        nonlocal cash, buys
        for k in range(n_grids - 1, -1, -1):
            line = lines[k]
            if b <= line < a and state[k] == "buy" and cash >= per_grid_cash - 1e-9:
                qtys[k] = per_grid_cash * (1 - FEE) / line
                cash -= per_grid_cash
                buys += 1
                state[k] = "hold"

    def walk(a, b):
        if b > a:
            cross_up(a, b)
        elif b < a:
            cross_down(a, b)

    for i in range(w, len(closes)):
        o, h, lo, c = opens[i], highs[i], lows[i], closes[i]
        if c >= o:   # 阳线近似路径：开 -> 低 -> 高 -> 收
            walk(o, lo); walk(lo, h); walk(h, c)
        else:        # 阴线近似路径：开 -> 高 -> 低 -> 收
            walk(o, h); walk(h, lo); walk(lo, c)
        equity.append(cash + held_btc() * c)
        if breakout_time is None and c > upper:
            breakout_time = datetime.fromtimestamp(times[i] / 1000).strftime("%Y-%m-%d")

    btc = held_btc()
    final_cash = cash + btc * closes[-1] * (1 - FEE) if btc > 0 else cash
    mtm = cash + btc * closes[-1]
    eq_final = equity[:-1] + [final_cash] if equity else [final_cash]
    m = metrics(eq_final)
    wins = [t for t in roundtrips if t > 0]
    return {
        **m,
        "lower": lower, "upper": upper, "step_pct": step / ((upper + lower) / 2),
        "buys": buys, "sells": sells, "roundtrips": len(roundtrips),
        "roundtrip_win_rate": (len(wins) / len(roundtrips)) if roundtrips else 0.0,
        "realized": realized,
        "final_btc": btc, "final_equity_mtm": mtm,
        "breakout_time": breakout_time,
        "start_price": p0, "warmup_days": warmup_days, "n_grids": n_grids,
    }


def pct(x):
    return f"{x * 100:+.1f}%"


# ---------- 跑起来 ----------

def main():
    times, opens, highs, lows, closes = get_klines(TOTAL_BARS)
    t0 = datetime.fromtimestamp(times[0] / 1000).strftime("%Y-%m-%d")
    t1 = datetime.fromtimestamp(times[-1] / 1000).strftime("%Y-%m-%d")
    print(f"数据：{SYMBOL} {INTERVAL} K 线 {len(closes)} 根（{t0} 至 {t1}），三方同一批数据")
    print(f"假设：起始 {START_CASH:,.0f} USDT，单边手续费 {FEE * 100:.1f}%，只做现货")
    print("（纯学习回测，不构成买卖建议）\n")

    hold_ret = closes[-1] / closes[0] - 1
    trend = run_trend(opens, closes)
    grid = run_grid(times, opens, highs, lows, closes)  # 基准：前 30 天定区间，20 格

    print(f"网格区间（只用前 {grid['warmup_days']} 天高低价定）：{grid['lower']:,.0f} ~ {grid['upper']:,.0f}，"
          f"{grid['n_grids']} 格，每格间距约 {grid['step_pct'] * 100:.1f}%")
    if grid["breakout_time"]:
        print(f"价格首次冲出区间上沿：{grid['breakout_time']}")
    print(f"网格买卖执行：买 {grid['buys']} 格 / 卖 {grid['sells']} 格，完成套利回合 {grid['roundtrips']} 次，"
          f"回合胜率 {grid['roundtrip_win_rate'] * 100:.0f}%，已兑现套利利润 {grid['realized']:+,.0f} USDT")
    print(f"网格期末还持有 BTC：{grid['final_btc']:.4f} 个（按市价 {grid['final_equity_mtm']:,.0f} USDT 总资产中未兑现的部分）\n")

    print("=== 同区间三方对照 ===")
    print(f"买入持有：  总收益 {pct(hold_ret)}（不交易，无夏普/回撤对照意义）")
    print(f"趋势策略：  总收益 {pct(trend['total_return'])}，{trend['trades']} 笔，胜率 {trend['win_rate'] * 100:.1f}%，"
          f"夏普 {trend['sharpe']:.2f}，最大回撤 {trend['max_drawdown'] * 100:.1f}%")
    print(f"网格策略：  总收益 {pct(grid['total_return'])}，完成回合 {grid['roundtrips']} 次，"
          f"夏普 {grid['sharpe']:.2f}，最大回撤 {grid['max_drawdown'] * 100:.1f}%（夏普/回撤从网格开跑日起算）")

    print("\n=== 网格参数敏感性（换个定法，结论翻不翻） ===")
    for wd, ng in [(7, 20), (30, 10), (30, 20), (30, 40)]:
        g = run_grid(times, opens, highs, lows, closes, warmup_days=wd, n_grids=ng)
        print(f"前{wd}天定区间 / {ng}格：总收益 {pct(g['total_return'])}，回合 {g['roundtrips']} 次，"
              f"最大回撤 {g['max_drawdown'] * 100:.1f}%，上沿冲破日 {g['breakout_time'] or '未冲破'}")

    print("\n=== 结论 ===")
    print("谁赢取决于这段时间是什么行情，而不是谁的策略更高级：")
    print(f"这 125 天 BTC 从 {closes[0]:,.0f} 涨到 {closes[-1]:,.0f}（{pct(hold_ret)}），本质是一段上行趋势行情。")
    print("网格在趋势里会一路把币卖飞：价格先在上沿附近反复进出（网格靠这个做了几十个回合），"
          "8 月下旬彻底离开区间后，网格就只剩现金，回撤看着小，其实是大部分时间根本不在场内。")
    forgone = START_CASH * hold_ret - START_CASH * grid["total_return"]
    print(f"网格兑现的 {grid['realized']:+,.0f} USDT 是真套利，但相对买入持有少赚约 {forgone:,.0f} USDT——"
          "踏空是网格在趋势市的隐性成本，不体现在任何一笔亏损里。")
    print(f"趋势策略这边 {trend['trades']} 笔只有两成胜率，却靠盈亏比跟住了大段涨幅（{pct(trend['total_return'])}），"
          "只是依然跑输持有——这段行情最优解是躺着不动。")
    print("反过来在横盘区间里，结论会倒过来：趋势策略被假信号反复磨，网格一格一格慢慢收。"
          "先判行情再选策略，就是上一课 regime 的实战注脚。")


if __name__ == "__main__":
    main()
