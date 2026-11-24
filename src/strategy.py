"""
量化策略模块（组员1 交付 · DMA-TF 双均线择时）
===============================================
来源：teammate_files/strategy-signals.py（配置层 + 信号层）
策略：双均线趋势择时 + 长期趋势过滤
  MA20 / MA60 / MA120
  买入：多头排列(MA20>MA60) 且 收盘价>MA120
  卖出：空头排列 或 跌破MA120
  信号滞后一日执行，杜绝未来函数
"""

from __future__ import annotations
from dataclasses import dataclass
import numpy as np
import pandas as pd


@dataclass(frozen=True)
class StrategyConfig:
    fast_window: int = 20
    slow_window: int = 60
    filter_window: int = 120
    price_col: str = "close"
    date_col: str = "date"

    def __post_init__(self):
        if not (0 < self.fast_window < self.slow_window < self.filter_window):
            raise ValueError("必须满足 0 < fast < slow < filter")


DEFAULT_CONFIG = StrategyConfig()
BENCHMARK_NAME = "沪深300（买入并持有）"
TARGET_NAME = "沪深300ETF（510300）"
BUY, SELL, HOLD = "buy", "sell", ""


def compute_indicators(df: pd.DataFrame, config: StrategyConfig = DEFAULT_CONFIG) -> pd.DataFrame:
    out = df.copy()
    close = out[config.price_col].astype(float)
    out["ma_fast"] = close.rolling(config.fast_window, min_periods=config.fast_window).mean()
    out["ma_slow"] = close.rolling(config.slow_window, min_periods=config.slow_window).mean()
    out["ma_filter"] = close.rolling(config.filter_window, min_periods=config.filter_window).mean()
    out["above_filter"] = close > out["ma_filter"]
    out["bullish"] = out["ma_fast"] > out["ma_slow"]
    return out


def generate_signals(df: pd.DataFrame, config: StrategyConfig = DEFAULT_CONFIG) -> pd.DataFrame:
    """生成带 position / trade 列的信号表。"""
    sig = compute_indicators(df, config)
    n = len(sig)
    target_state = np.zeros(n, dtype=int)
    holding = 0
    for i in range(n):
        bullish = bool(sig["bullish"].iloc[i])
        above = bool(sig["above_filter"].iloc[i])
        ready = not (
            np.isnan(sig["ma_fast"].iloc[i])
            or np.isnan(sig["ma_slow"].iloc[i])
            or np.isnan(sig["ma_filter"].iloc[i])
        )
        if holding == 0:
            if ready and bullish and above:
                holding = 1
        else:
            if not bullish or not above:
                holding = 0
        target_state[i] = holding

    sig["target_state"] = target_state
    sig["position"] = np.concatenate(([0], target_state[:-1]))  # 滞后一日，防未来函数
    sig["trade"] = HOLD
    sig.loc[sig["position"].diff().fillna(0) > 0, "trade"] = BUY
    sig.loc[sig["position"].diff().fillna(0) < 0, "trade"] = SELL
    return sig
