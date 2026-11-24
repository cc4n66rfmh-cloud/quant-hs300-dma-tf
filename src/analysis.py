"""
回测结果分析模块（组员4 交付 · 指标计算）
==========================================
来源：teammate_files/finalanalysis(1).py
计算四项必需指标：累计收益率、年化收益率、最大回撤、夏普比率
基准：沪深300（买入并持有），无风险利率 rf=0.02，年交易日 250
"""

import numpy as np

RF = 0.02
ANNUAL_TRADE_DAYS = 250


def max_drawdown(series) -> float:
    peak = series.cummax()
    drawdown = (series - peak) / peak
    return float(drawdown.min())


def _metrics_for(nav, ret, days) -> dict:
    final_nav = float(nav.iloc[-1])
    cum_ret = float((1 + ret.fillna(0)).prod() - 1)
    annual_ret = final_nav ** (365 / days) - 1 if days > 0 else np.nan
    mdd = max_drawdown(nav)
    excess = ret - RF / ANNUAL_TRADE_DAYS
    ann_excess_mean = excess.mean() * ANNUAL_TRADE_DAYS
    ann_std = ret.std() * np.sqrt(ANNUAL_TRADE_DAYS)
    sharpe = ann_excess_mean / ann_std if ann_std != 0 else np.nan
    return {
        "累计收益率": cum_ret,
        "年化收益率": float(annual_ret),
        "最大回撤": mdd,
        "夏普比率": float(sharpe),
    }


def compute_metrics(equity) -> dict:
    """
    输入：equity DataFrame（含 date / strategy_nav / benchmark_nav）
    输出：{'策略': {四项指标}, '基准': {四项指标}}
    """
    equity = equity.sort_values("date").reset_index(drop=True)
    days = (equity["date"].iloc[-1] - equity["date"].iloc[0]).days

    strategy_ret = equity["strategy_nav"].pct_change()
    benchmark_ret = equity["benchmark_nav"].pct_change()

    return {
        "策略": _metrics_for(equity["strategy_nav"], strategy_ret, days),
        "基准": _metrics_for(equity["benchmark_nav"], benchmark_ret, days),
    }
