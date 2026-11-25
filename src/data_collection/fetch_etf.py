"""
数据获取与处理模块（组员2 交付）
=====================================================
分工：数据获取与处理
数据源：akshare（东方财富）免费接口 fund_etf_hist_em，无需注册/token
标的：  沪深300ETF（510300）
区间：  2018-01-01 ~ 2024-12-31（1699 个交易日）
复权：  前复权 qfq，避免除权跳空造成假信号

流程：下载 → 清洗（去无效价/去重/转数值）→ 落盘到 data/raw/

运行：
    python src/data_collection/fetch_etf.py

输出：
    data/raw/etf_510300_data.csv
    列：date, code, open, high, low, close, volume, amount
"""

from __future__ import annotations
import os
import sys

import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RAW_DIR = os.path.join(BASE_DIR, "data", "raw")
RAW_PATH = os.path.join(RAW_DIR, "etf_510300_data.csv")

TARGET_CODE = "sh.510300"
START_DATE = "20180101"
END_DATE = "20241231"
ADJUST = "qfq"

# akshare 中文列名 -> 引擎使用的英文列名
COL_MAP = {
    "日期": "date",
    "开盘": "open",
    "最高": "high",
    "最低": "low",
    "收盘": "close",
    "成交量": "volume",
    "成交额": "amount",
}
KEEP_COLS = ["date", "code", "open", "high", "low", "close", "volume", "amount"]


def fetch_etf_daily(symbol: str = "510300", start: str = START_DATE,
                    end: str = END_DATE, adjust: str = ADJUST) -> pd.DataFrame:
    """从 akshare 下载 ETF 日线，清洗后返回标准列结构的 DataFrame。"""
    try:
        import akshare as ak
    except ImportError:
        raise RuntimeError(
            "缺少 akshare，请先运行：pip install akshare -i https://mirrors.aliyun.com/pypi/simple/"
        )

    raw = ak.fund_etf_hist_em(
        symbol=symbol, period="daily",
        start_date=start, end_date=end, adjust=adjust,
    )
    if raw is None or raw.empty:
        raise RuntimeError(f"akshare 未返回 {symbol} 的数据，请检查代码或网络")

    df = raw.rename(columns=COL_MAP).copy()
    for col in COL_MAP.values():
        if col not in df.columns:
            raise RuntimeError(f"下载数据缺少必要列：{col}，实际列：{list(df.columns)}")

    df["date"] = pd.to_datetime(df["date"])
    for col in ["open", "high", "low", "close", "volume", "amount"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # 清洗：去掉无效价格行、重复日期，按日期升序
    df = df[df["close"] > 0]
    df = df.drop_duplicates(subset=["date"], keep="last")
    df = df.sort_values("date").reset_index(drop=True)
    df["code"] = TARGET_CODE

    return df[KEEP_COLS]


def save_raw(df: pd.DataFrame, path: str = RAW_PATH) -> str:
    """落盘到 data/raw/，返回文件路径。"""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    df.to_csv(path, index=False, encoding="utf-8-sig")
    return path


def load_or_fetch(path: str = RAW_PATH) -> pd.DataFrame:
    """本地优先：已有落盘数据则直接读取，缺失时才联网下载。
    这样答辩现场即使断网或接口限流，也能从原始数据完整重跑。"""
    if os.path.exists(path):
        df = pd.read_csv(path)
        df["date"] = pd.to_datetime(df["date"])
        df = df.sort_values("date").reset_index(drop=True)
        print(f"      读取本地原始数据：{path}（{len(df)} 行）")
        return df[KEEP_COLS]
    print("      本地无缓存，联网下载 ...")
    df = fetch_etf_daily()
    save_raw(df, path)
    return df


def main() -> int:
    print(">>> 1. 从 akshare（东方财富）下载沪深300ETF(510300) 日线 ...")
    try:
        df = fetch_etf_daily()
    except Exception as exc:  # noqa: BLE001
        print(f"❌ 数据接入失败：{exc}")
        return 1

    print(f">>> 2. 清洗完成：{len(df)} 行，"
          f"{df['date'].min().date()} ~ {df['date'].max().date()}")
    path = save_raw(df)
    print(f">>> 3. 原始数据已落盘：{path}")
    print(df.head(3).to_string(index=False))
    print("\n数据获取完成，可运行 python rebuild_from_raw.py 从零重跑回测。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
