"""
回测引擎模块（组员3 交付 · 事件驱动）
======================================
来源：teammate_files/backtest_engine.py
逐日盯市，含佣金(万2.5,最低5元)、印花税(千1,卖出)、滑点(万1)，A股100股整数倍。

说明：日常展示走 main.py 的主线（直接读组员3已生成的 equity_curve.csv）。
本模块保留"从原始行情重跑回测"的能力，用于答辩时证明内核真实可运行。
需要原始行情 etf_510300_data.csv（向组员3索取）。
"""

import pandas as pd


class BacktestEngine:
    def __init__(self, initial_capital=1_000_000.0, commission_rate=0.00025,
                 min_commission=5.0, stamp_duty_rate=0.001, slippage=0.0001):
        self.initial_capital = initial_capital
        self.commission_rate = commission_rate
        self.min_commission = min_commission
        self.stamp_duty_rate = stamp_duty_rate
        self.slippage = slippage

    def run(self, df_signals: pd.DataFrame):
        """输入带 trade 列(buy/sell/'')的信号表，返回 (equity, trades) 两个 DataFrame。"""
        cash, shares = self.initial_capital, 0
        trades, equity_records = [], []

        for i in range(len(df_signals)):
            date = df_signals.loc[i, "date"]
            open_price = df_signals.loc[i, "open"]
            close_price = df_signals.loc[i, "close"]
            signal = df_signals.loc[i, "trade"]

            if signal == "buy" and cash > 0:
                exec_price = open_price * (1 + self.slippage)
                max_shares = int(cash / (exec_price * (1 + self.commission_rate)) // 100) * 100
                if max_shares > 0:
                    amount = max_shares * exec_price
                    commission = max(amount * self.commission_rate, self.min_commission)
                    if amount + commission <= cash:
                        cash -= amount + commission
                        shares += max_shares
                        trades.append({"日期": date, "动作": "买入",
                                       "成交价": round(exec_price, 4), "数量": max_shares})
            elif signal == "sell" and shares > 0:
                exec_price = open_price * (1 - self.slippage)
                amount = shares * exec_price
                commission = max(amount * self.commission_rate, self.min_commission)
                stamp_duty = amount * self.stamp_duty_rate
                cash += amount - commission - stamp_duty
                trades.append({"日期": date, "动作": "卖出",
                               "成交价": round(exec_price, 4), "数量": shares})
                shares = 0

            equity_records.append({"date": date, "total_asset": cash + shares * close_price})

        return pd.DataFrame(equity_records), pd.DataFrame(trades)


def run_backtest(df_signals, capital=1_000_000.0, fee=0.00025):
    """便捷函数：返回 (equity, trades)。"""
    return BacktestEngine(initial_capital=capital, commission_rate=fee).run(df_signals)
