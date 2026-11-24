import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# ==========读取数据==========
equity = pd.read_csv("equity_curve.csv")
trade = pd.read_csv("trade_log.csv")

# 转日期
equity["date"] = pd.to_datetime(equity["date"])
equity = equity.sort_values("date").reset_index(drop=True)

# ==========计算每日收益率 & 每日累计收益率==========
equity["strategy_ret"] = equity["strategy_nav"].pct_change()
equity["benchmark_ret"] = equity["benchmark_nav"].pct_change()

# 完整每日累计收益率
equity["cum_strategy_ret"] = (1 + equity["strategy_ret"]).cumprod() - 1
equity["cum_benchmark_ret"] = (1 + equity["benchmark_ret"]).cumprod() - 1

# 期末累计收益率（就是报告要填那一个）
cum_ret_strategy = equity["cum_strategy_ret"].iloc[-1]
cum_ret_benchmark = equity["cum_benchmark_ret"].iloc[-1]

# 无风险收益率
rf = 0.02
annual_trade_days = 250

# ==========基础指标计算==========
final_strategy = equity["strategy_nav"].iloc[-1]
final_benchmark = equity["benchmark_nav"].iloc[-1]

days = (equity["date"].iloc[-1] - equity["date"].iloc[0]).days
annual_strategy = (final_strategy) ** (365 / days) - 1
annual_benchmark = (final_benchmark) ** (365 / days) - 1

# 最大回撤
def max_drawdown(series):
    peak = series.cummax()
    drawdown = (series - peak) / peak
    return drawdown.min()

md_strategy = max_drawdown(equity["strategy_nav"])
md_benchmark = max_drawdown(equity["benchmark_nav"])

# ==========夏普比率==========
excess_strategy = equity["strategy_ret"] - rf / annual_trade_days
ann_excess_mean = excess_strategy.mean() * annual_trade_days
ann_std_strategy = equity["strategy_ret"].std() * np.sqrt(annual_trade_days)
sharpe_strategy = ann_excess_mean / ann_std_strategy if ann_std_strategy != 0 else np.nan

excess_benchmark = equity["benchmark_ret"] - rf / annual_trade_days
ann_excess_mean_bm = excess_benchmark.mean() * annual_trade_days
ann_std_bm = equity["benchmark_ret"].std() * np.sqrt(annual_trade_days)
sharpe_benchmark = ann_excess_mean_bm / ann_std_bm if ann_std_bm != 0 else np.nan

# ==========交易指标==========
total_trade = len(trade)
win_num = len(trade[trade["动作"] == "卖出"])
win_rate = win_num / total_trade if total_trade > 0 else 0

# ==========输出结果==========
print("=====策略绩效报告=====")
print(f"策略最终净值：{final_strategy:.4f}")
print(f"基准最终净值：{final_benchmark:.4f}")
print()
print(f"策略累计收益率：{cum_ret_strategy:.4f}")
print(f"基准累计收益率：{cum_ret_benchmark:.4f}")
print()
print(f"策略年化收益率：{annual_strategy:.4f}")
print(f"基准年化收益率：{annual_benchmark:.4f}")
print()
print(f"策略最大回撤：{md_strategy:.4f}")
print(f"基准最大回撤：{md_benchmark:.4f}")
print()
print(f"策略夏普比率：{sharpe_strategy:.4f}")
print(f"基准夏普比率：{sharpe_benchmark:.4f}")
print()
print(f"总交易次数：{total_trade}")
print(f"卖出次数：{win_num}")
print(f"胜率：{win_rate:.4f}")

# ==========绘制净值曲线==========
plt.rcParams["font.sans-serif"] = ["SimHei"]
plt.rcParams["axes.unicode_minus"] = False

plt.figure(figsize=(12, 6))
plt.plot(equity["date"], equity["strategy_nav"], label="策略净值", color="#E53935")
plt.plot(equity["date"], equity["benchmark_nav"], label="沪深 300 基准", color="#1E88E5")
plt.title("策略与基准净值对比曲线")
plt.xlabel("日期")
plt.ylabel("净值")
plt.legend()
plt.grid(alpha=0.3)
plt.tight_layout()
plt.show()
