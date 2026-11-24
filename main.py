"""
量化交易系统 - 统一入口
=======================
运行方式：python main.py

把 5 位组员的成果串成一条流水线：
    组员2 数据 -> 组员1 策略 -> 组员3 回测 -> 组员4 分析 -> 组员5 展示

主线：读取组员3/4 已生成的真实回测结果（equity_curve.csv + trade_log.csv），
      计算指标、出图、出表。这条链路稳定可复现。
"""

from src import data, analysis, display


def main():
    print("=" * 64)
    print("  量化交易系统启动（沪深300ETF · DMA-TF 双均线择时）")
    print("=" * 64)

    # ---------- 1. 加载回测结果（来自组员3/4）----------
    print("\n[1/4] 加载回测结果 ...")
    equity = data.load_equity_curve()      # data/processed/equity_curve.csv
    trades = data.load_trade_log()         # data/processed/trade_log.csv
    print(f"      净值数据 {len(equity)} 行，成交记录 {len(trades)} 笔")

    # ---------- 2. 计算指标（组员4 的口径）----------
    print("[2/4] 计算回测指标 ...")
    metrics = analysis.compute_metrics(equity)

    # ---------- 3. 展示（你负责）----------
    print("[3/4] 输出指标表 ...")
    display.show_metrics(metrics)

    print("[4/4] 绘制净值对比图 ...")
    display.plot_equity(equity, trades=trades)

    print("\n" + "=" * 64)
    print("  完成！结果已保存到 outputs/ 文件夹：")
    print("    - 指标对照表.csv")
    print("    - 净值对比图.png")
    print("=" * 64)


if __name__ == "__main__":
    main()
