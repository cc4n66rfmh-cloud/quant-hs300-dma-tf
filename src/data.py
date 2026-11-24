"""
数据加载模块（组员5 整合 · 数据来自组员2/3）
=============================================
作用：把组员3/4 已生成的回测结果文件读进来，供展示层使用。
- equity_curve.csv：每日净值（策略 + 基准）
- trade_log.csv：成交流水（日期、动作、成交价、数量）
"""

import os
import pandas as pd

# 用 __file__ 定位，避免"在哪个文件夹运行"导致找不到文件
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROCESSED_DIR = os.path.join(BASE_DIR, "data", "processed")


def load_equity_curve(path: str = None) -> pd.DataFrame:
    """读取净值曲线，返回带 date / strategy_nav / benchmark_nav 的 DataFrame。"""
    path = path or os.path.join(PROCESSED_DIR, "equity_curve.csv")
    df = pd.read_csv(path)
    df["date"] = pd.to_datetime(df["date"])
    return df.sort_values("date").reset_index(drop=True)


def load_trade_log(path: str = None) -> pd.DataFrame:
    """读取成交流水，返回带 日期 / 动作 / 成交价 / 数量 的 DataFrame。"""
    path = path or os.path.join(PROCESSED_DIR, "trade_log.csv")
    df = pd.read_csv(path)
    df["日期"] = pd.to_datetime(df["日期"])
    return df
