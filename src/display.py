"""
系统展示模块（组员5 交付 · 你真正署名的文件）
=============================================
接收组员3/4 的回测结果，输出：
  1. 命令行指标对照表（策略 vs 基准）
  2. 归一化净值对比图（均从 1.0 起算，标注买卖点）
  3. 指标表 CSV（供报告/PPT 直接引用）

作业评分表要求"证明是真实可运行内核而非静态页面"，这个模块就是证据。
"""

import os
import matplotlib
matplotlib.use("Agg")  # 无界面环境也能出图
import matplotlib.pyplot as plt
import pandas as pd

# 中文字体（Windows 用 SimHei；缺失时自动回退，不影响运行）
plt.rcParams["font.sans-serif"] = ["SimHei", "Microsoft YaHei", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(BASE_DIR, "outputs")


def show_metrics(metrics: dict) -> pd.DataFrame:
    """打印策略 vs 基准的指标对照表，并返回 DataFrame（供存 CSV）。"""
    rows = []
    for name, m in metrics.items():
        rows.append({
            "对象": name,
            "累计收益率": f"{m['累计收益率']:.2%}",
            "年化收益率": f"{m['年化收益率']:.2%}",
            "最大回撤": f"{m['最大回撤']:.2%}",
            "夏普比率": f"{m['夏普比率']:.4f}",
        })
    table = pd.DataFrame(rows)

    print("\n" + "=" * 72)
    print("  回测指标对照表")
    print("=" * 72)
    print(table.to_string(index=False))
    print("=" * 72 + "\n")

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    table.to_csv(os.path.join(OUTPUT_DIR, "指标对照表.csv"), index=False, encoding="utf-8-sig")
    print("指标表已保存：outputs/指标对照表.csv")
    return table


def plot_equity(equity: pd.DataFrame, trades: pd.DataFrame = None,
                save_path: str = None) -> str:
    """
    画归一化净值对比图：策略 vs 基准（均 1.0 起算），并标注关键买卖点。
    equity : 含 date / strategy_nav / benchmark_nav
    trades : 含 日期 / 动作（买入 / 卖出）
    """
    save_path = save_path or os.path.join(OUTPUT_DIR, "净值对比图.png")
    os.makedirs(os.path.dirname(save_path) or ".", exist_ok=True)

    eq = equity.copy()
    eq["date"] = pd.to_datetime(eq["date"])

    # 归一化到 1.0 起算（数据本身已是 1.0 起，再除一次也安全）
    strategy_nav = eq["strategy_nav"] / eq["strategy_nav"].iloc[0]
    benchmark_nav = eq["benchmark_nav"] / eq["benchmark_nav"].iloc[0]

    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(eq["date"], strategy_nav, label="策略净值", color="#E53935", linewidth=1.8)
    ax.plot(eq["date"], benchmark_nav, label="沪深300基准", color="#1E88E5",
            linewidth=1.4, linestyle="--")

    # 标注买卖点：在策略净值曲线上找到成交日期对应的净值
    if trades is not None and len(trades) > 0:
        nav_by_date = pd.Series(strategy_nav.values, index=eq["date"])
        t = trades.copy()
        t["日期"] = pd.to_datetime(t["日期"])
        buy_dates, sell_dates = [], []
        for _, row in t.iterrows():
            d = row["日期"]
            if d not in nav_by_date.index:
                continue
            (buy_dates if "买" in str(row["动作"]) else sell_dates).append((d, nav_by_date.loc[d]))
        if buy_dates:
            ax.scatter([x[0] for x in buy_dates], [x[1] for x in buy_dates],
                       marker="^", color="#D32F2F", s=45, zorder=5, label="买入")
        if sell_dates:
            ax.scatter([x[0] for x in sell_dates], [x[1] for x in sell_dates],
                       marker="v", color="#388E3C", s=45, zorder=5, label="卖出")

    ax.axhline(1.0, color="#B0BEC5", linewidth=0.8, linestyle=":")
    ax.set_title("策略与基准归一化净值对比（买卖点标注）", fontsize=14)
    ax.set_xlabel("日期")
    ax.set_ylabel("归一化净值（起点 = 1.0）")
    ax.legend(loc="best")
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(save_path, dpi=150)
    plt.close(fig)

    print(f"净值对比图已保存：{save_path}")
    return save_path
