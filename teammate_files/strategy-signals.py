"""DMA-TF 策略 · 一体化单文件版（配置 + 信号 + 演示）
=====================================================
  三层职责：

    第一部分  配置层（原 strategy/config.py）
        StrategyConfig / BacktestPeriods / 默认实例 / 常量
    第二部分  信号层（原 strategy/dual_ma_timing.py，核心交付物）
        validate_input / compute_indicators / generate_signals
        get_trade_log / split_period
    第三部分  演示层（原 examples/demo_signals.py）
        make_synthetic_market / quick_equity / main

依赖方向：配置层 → 信号层 → 演示层（单向向下，无循环依赖）。

------------------------------------------------------------------
策略全称：双均线趋势择时 + 长期趋势过滤
(Dual Moving Average Timing with Trend Filter, DMA-TF)
方法归属：技术面择时 / 趋势跟踪 / 动量效应

信号规则（收盘后计算，次一交易日执行，严格避免未来函数）：
    指标 MA_fast   = SMA(close, 20)   短期趋势
         MA_slow   = SMA(close, 60)   中期趋势
         MA_filter = SMA(close, 120)  长期趋势过滤线
    买入（空仓→满仓）：多头排列 MA_fast > MA_slow 且 close > MA_filter
    卖出（满仓→空仓）：空头排列 MA_fast < MA_slow 或 close < MA_filter
    仓位：满仓(1) / 空仓(0)，不加杠杆、不做空（符合 A 股现货现实）

说明：采用「均线状态(level)」而非「交叉那一根K线(cross event)」作为判据，
避免金叉与站上长期线不同步时永远无法入场的问题。golden_cross/death_cross
事件列仍保留，供报告绘图与逐笔解释使用。

接口约定（供组员3 的回测引擎对接）：
    position[t] = target_state[t-1]，即 t-1 日收盘后决策、t 日建/平仓。
    策略 t 日收益 = position[t] * (close[t] / close[t-1] - 1)。
    回测引擎消费 position 算收益、trade 画买卖点；
    无需重复实现择时逻辑，手续费/滑点按 trade 的发生日另行扣除。

------------------------------------------------------------------
运行方式（在 quant_project 目录）：
    python dma_tf_strategy.py

注意：演示部分的净值基于合成数据，仅验证代码正确性与对接接口，
不是真实业绩。完整回测由组员3 的引擎用历史数据完成。

作者：组员1（量化策略设计）
"""

from __future__ import annotations

import os
from dataclasses import dataclass

import numpy as np
import pandas as pd


# ==================================================================
# 第一部分：配置层
# 职责：集中管理全部参数，作为全项目「单一配置源」，保证可复现性。
# ==================================================================

@dataclass(frozen=True)
class StrategyConfig:
    """DMA-TF 策略的不可变配置对象。

    Attributes
    ----------
    fast_window : int
        短期均线窗口（默认20，约一个月交易日），用于捕捉短期趋势拐点。
    slow_window : int
        长期均线窗口（默认60，约一个季度交易日），用于确认中期趋势方向。
    filter_window : int
        长期趋势过滤均线窗口（默认120，约半年交易日）。
        价格站上该均线才允许开仓，避免在长期下跌趋势中做多。
    price_col : str
        K线中收盘价列名，信号全部基于收盘价计算。
    date_col : str
        日期列名。
    """

    fast_window: int = 20
    slow_window: int = 60
    filter_window: int = 120
    price_col: str = "close"
    date_col: str = "date"

    def __post_init__(self) -> None:
        """校验参数合法性，早失败早暴露。"""
        if not (0 < self.fast_window < self.slow_window < self.filter_window):
            raise ValueError(
                "必须满足 0 < fast_window < slow_window < filter_window，"
                f"当前为 {self.fast_window}/{self.slow_window}/{self.filter_window}"
            )


@dataclass(frozen=True)
class BacktestPeriods:
    """样本内 / 样本外区间定义（用于稳健性检验，防止过拟合）。

    样本内用于观察策略表现与参数讨论；样本外完全不参与任何参数选择，
    仅用于最终验证策略是否具备泛化能力。
    """

    in_sample_start: str = "2010-01-01"
    in_sample_end: str = "2018-12-31"
    out_sample_start: str = "2019-01-01"
    out_sample_end: str = "2024-12-31"


# 默认配置实例：全项目统一引用这一个即可
DEFAULT_CONFIG = StrategyConfig()
DEFAULT_PERIODS = BacktestPeriods()

# 基准说明：本策略为指数择时，基准选定为「买入并持有沪深300」
BENCHMARK_NAME = "沪深300（买入并持有）"
TARGET_NAME = "沪深300ETF（510300）"


# ==================================================================
# 第二部分：信号层
# 职责：把行情表变成带 position / trade / reason 的信号表。
# ==================================================================

# 交易标记常量
BUY = "buy"
SELL = "sell"
HOLD = ""

# 信号成因说明（便于答辩时逐笔解释）
REASON_BUY = "多头排列且站上120日线"
REASON_SELL_DEATH = "死叉(空头排列)"
REASON_SELL_FILTER = "跌破120日线"


def validate_input(df: pd.DataFrame, config: StrategyConfig = DEFAULT_CONFIG) -> None:
    """校验输入数据是否包含策略所需列，缺失则抛出清晰错误。"""
    required = {config.date_col, config.price_col}
    missing = required - set(df.columns)
    if missing:
        raise KeyError(f"输入数据缺少必需列：{sorted(missing)}；现有列：{list(df.columns)}")
    if df[config.price_col].isna().all():
        raise ValueError(f"价格列 {config.price_col!r} 全为空，无法计算信号。")


def compute_indicators(
    df: pd.DataFrame, config: StrategyConfig = DEFAULT_CONFIG
) -> pd.DataFrame:
    """计算均线指标与原始交叉/趋势事件（不改变行数）。

    Parameters
    ----------
    df : DataFrame
        至少包含 date 与 close 列，按日期升序排列。
    config : StrategyConfig
        策略参数。

    Returns
    -------
    DataFrame
        原数据副本，新增列：ma_fast, ma_slow, ma_filter,
        golden_cross, death_cross, above_filter, bullish。
    """
    validate_input(df, config)
    out = df.copy()
    close = out[config.price_col].astype(float)

    out["ma_fast"] = close.rolling(config.fast_window, min_periods=config.fast_window).mean()
    out["ma_slow"] = close.rolling(config.slow_window, min_periods=config.slow_window).mean()
    out["ma_filter"] = close.rolling(
        config.filter_window, min_periods=config.filter_window
    ).mean()

    # 交叉事件：今日快线在慢线上/下方，且昨日相反
    out["golden_cross"] = (out["ma_fast"] > out["ma_slow"]) & (
        out["ma_fast"].shift(1) <= out["ma_slow"].shift(1)
    )
    out["death_cross"] = (out["ma_fast"] < out["ma_slow"]) & (
        out["ma_fast"].shift(1) >= out["ma_slow"].shift(1)
    )
    out["above_filter"] = close > out["ma_filter"]
    # 多头/空头排列状态（用于状态机判据）
    out["bullish"] = out["ma_fast"] > out["ma_slow"]

    return out


def generate_signals(
    df: pd.DataFrame, config: StrategyConfig = DEFAULT_CONFIG
) -> pd.DataFrame:
    """生成 DMA-TF 策略的完整信号表（组员2/3 对接主入口）。

    Parameters
    ----------
    df : DataFrame
        OHLCV 行情数据，需含 date、close 列，按日期升序。
    config : StrategyConfig
        策略参数。

    Returns
    -------
    DataFrame
        在 compute_indicators 结果基础上新增：
        target_state : int  当日收盘后做出的目标仓位决策(0/1)
        position     : int  当日实际持仓(0/1)，= target_state 昨日值，无未来函数
        trade        : str  'buy' / 'sell' / ''，标记建/平仓日
        reason       : str  交易成因说明
    """
    sig = compute_indicators(df, config)
    n = len(sig)
    target_state = np.zeros(n, dtype=int)
    reason = np.array([""] * n, dtype=object)

    # 状态机：维护当前是否持仓（决策序列，position 由它滞后一日得到）
    holding = 0
    for i in range(n):
        bullish = bool(sig["bullish"].iloc[i])
        above = bool(sig["above_filter"].iloc[i])
        # 指标尚未成熟（NaN）时不允许任何交易
        ready = not (
            np.isnan(sig["ma_fast"].iloc[i])
            or np.isnan(sig["ma_slow"].iloc[i])
            or np.isnan(sig["ma_filter"].iloc[i])
        )

        if holding == 0:
            if ready and bullish and above:
                holding = 1
                reason[i] = REASON_BUY
        else:  # holding == 1
            if not bullish:
                holding = 0
                reason[i] = REASON_SELL_DEATH
            elif not above:
                holding = 0
                reason[i] = REASON_SELL_FILTER

        target_state[i] = holding

    sig["target_state"] = target_state
    # 关键：实际持仓滞后一日，杜绝未来函数
    sig["position"] = np.concatenate(([0], target_state[:-1]))
    sig["trade"] = HOLD
    sig.loc[sig["position"].diff().fillna(0) > 0, "trade"] = BUY
    sig.loc[sig["position"].diff().fillna(0) < 0, "trade"] = SELL
    # 把成因对齐到实际成交日（比决策日晚一日）
    shifted_reason = np.concatenate(([""], reason[:-1]))
    sig["reason"] = shifted_reason

    return sig


def get_trade_log(signals: pd.DataFrame, config: StrategyConfig = DEFAULT_CONFIG) -> pd.DataFrame:
    """导出简洁的买卖流水，便于核对与在净值曲线上标注。"""
    trades = signals[signals["trade"] != HOLD][
        [config.date_col, config.price_col, "trade", "reason"]
    ].copy()
    trades = trades.rename(
        columns={config.date_col: "日期", config.price_col: "收盘价", "trade": "动作", "reason": "成因"}
    )
    return trades.reset_index(drop=True)


def split_period(signals: pd.DataFrame, start: str, end: str, date_col: str = "date") -> pd.DataFrame:
    """按日期区间切分样本（供样本内/样本外检验）。"""
    mask = (signals[date_col] >= start) & (signals[date_col] <= end)
    return signals.loc[mask].copy()


# ==================================================================
# 第三部分：演示层
# 职责：无网络环境下证明信号代码正确、接口可对接。
# ==================================================================

def make_synthetic_market(n: int = 1500, seed: int = 42) -> pd.DataFrame:
    """生成带牛熊周期的合成日线数据（闭式、可复现），用于无网络环境下演示。"""
    rng = np.random.default_rng(seed)
    dates = pd.bdate_range("2015-01-01", periods=n)
    t = np.arange(n)
    # 长期慢牛 + 两轮明显的牛熊周期，制造充足的金叉/死叉与趋势破坏场景
    drift = 0.0006 * t
    cycle = 0.18 * np.sin(2 * np.pi * t / 300)      # 中期周期（牛熊切换）
    cycle += 0.06 * np.sin(2 * np.pi * t / 95)      # 短周期噪声
    drawdown = -0.22 * np.exp(-((t - 520) ** 2) / (2 * 70**2))   # 快速深跌
    drawdown += -0.18 * np.exp(-((t - 1080) ** 2) / (2 * 80**2))
    log_price = 4.6 + drift / 10 + cycle + drawdown
    noise = np.cumsum(rng.normal(0, 0.003, n))
    close = np.exp(log_price + noise) * 100

    df = pd.DataFrame({"date": dates, "close": close})
    df["open"] = df["close"].shift(1).fillna(df["close"].iloc[0])
    df["high"] = df[["open", "close"]].max(axis=1) * 1.01
    df["low"] = df[["open", "close"]].min(axis=1) * 0.99
    df["volume"] = rng.integers(1_000_000, 5_000_000, n)
    return df[["date", "open", "high", "low", "close", "volume"]]


def quick_equity(signals: pd.DataFrame) -> pd.DataFrame:
    """自检用：按 position[t]*收益[t] 累计净值（不含成本）。"""
    out = signals.copy()
    out["asset_ret"] = out["close"].pct_change().fillna(0.0)
    out["strategy_ret"] = out["position"] * out["asset_ret"]
    out["strategy_nav"] = (1 + out["strategy_ret"]).cumprod()
    out["benchmark_nav"] = (1 + out["asset_ret"]).cumprod()
    return out


def main() -> None:
    cfg = DEFAULT_CONFIG
    df = make_synthetic_market()
    print(f"[数据] 合成行情 {len(df)} 根K线，区间 {df['date'].min()} ~ {df['date'].max()}")

    sig = generate_signals(df, cfg)
    # 自检断言：position 必须是 target_state 滞后一日，且取值仅 0/1
    assert set(sig["position"].unique()) <= {0, 1}
    assert (sig["position"].iloc[1:].to_numpy() == sig["target_state"].iloc[:-1].to_numpy()).all()

    trades = get_trade_log(sig, cfg)
    print(f"\n[信号] 共产生 {len(trades)} 笔交易，前12笔如下：")
    print(trades.head(12).to_string(index=False))

    eq = quick_equity(sig)
    last = eq.iloc[-1]
    print("\n[自检] 策略/基准期末净值（不含成本，仅验证方向）：")
    print(f"  策略净值 = {last['strategy_nav']:.4f}   基准净值 = {last['benchmark_nav']:.4f}")

    ins = split_period(sig, DEFAULT_PERIODS.in_sample_start, DEFAULT_PERIODS.in_sample_end)
    outs = split_period(sig, DEFAULT_PERIODS.out_sample_start, DEFAULT_PERIODS.out_sample_end)
    print(f"\n[样本] 样本内 {len(ins)} 行 / 样本外 {len(outs)} 行（合成数据仅演示切分接口）")

    # 留存一份带信号的样例数据，供组员2/3 对接参考
    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "sample_signals.csv")
    sig.to_csv(out_path, index=False, encoding="utf-8-sig")
    print(f"\n[输出] 带信号的样例数据已写入 {os.path.normpath(out_path)}")


if __name__ == "__main__":
    main()
