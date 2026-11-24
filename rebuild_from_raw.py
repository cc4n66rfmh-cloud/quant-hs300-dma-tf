"""
从零复现脚本（组员5 整合 · 全链路证据）
========================================
一条命令走完老师要求的完整链路：
    数据接入 → 策略信号 → 回测引擎 → 结果分析 → 展示输出

与 main.py 的区别：
  - main.py：读取组员3已生成的回测结果（日常展示用，秒出）
  - rebuild_from_raw.py：从 akshare 原始行情开始重跑（答辩证明"真实内核"用）

运行：
    pip install -r requirements.txt
    python rebuild_from_raw.py
"""

from __future__ import annotations
import os
import sys

import pandas as pd

from src.data_fetch import fetch_etf_daily, save_raw, RAW_PATH
from src.strategy import generate_signals, DEFAULT_CONFIG
from src.backtest import BacktestEngine
from src.analysis import compute_metrics
from src.display import show_metrics, plot_equity


def build_equity(raw: pd.DataFrame, engine: BacktestEngine) -> pd.DataFrame:
    """信号 → 回测 → 净值曲线（策略 + 基准）。"""
    sig = generate_signals(raw.copy(), DEFAULT_CONFIG).reset_index(drop=True)
    equity, _trades = engine.run(sig)
    equity["strategy_nav"] = equity["total_asset"] / engine.initial_capital
    equity["benchmark_nav"] = sig["close"] / sig["close"].iloc[0]
    return equity


def main() -> int:
    print("=" * 72)
    print("  全链路复现：原始行情 → 信号 → 回测 → 指标 → 出图")
    print("=" * 72)

    # 1. 数据接入
    print("\n[1/5] 数据接入：从 akshare 下载 510300 原始日线 ...")
    try:
        raw = fetch_etf_daily()
    except Exception as exc:  # noqa: BLE001
        print(f"❌ 数据接入失败：{exc}")
        return 1
    save_raw(raw)
    print(f"      {len(raw)} 行，{raw['date'].min().date()} ~ {raw['date'].max().date()}")

    # 2~3. 策略信号 + 回测
    print("[2/5] 策略信号：DMA-TF 双均线择时（MA20/60/120，滞后一日）")
    print("[3/5] 回测引擎：逐日盯市，含佣金/印花税/滑点")
    engine = BacktestEngine()
    equity = build_equity(raw, engine)

    # 4. 指标分析
    print("[4/5] 指标计算 ...")
    metrics = compute_metrics(equity)
    show_metrics(metrics)

    # 5. 展示出图
    print("[5/5] 生成净值对比图 ...")
    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            "outputs", "净值对比图_全链路复现.png")
    plot_equity(equity, save_path=out_path)

    print("\n✅ 全链路复现完成。这证明系统有真实可运行内核，而非静态展示页。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
