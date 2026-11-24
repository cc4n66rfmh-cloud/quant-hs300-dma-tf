# ==================================================================
# 完整回测系统 (策略逻辑 + 回测引擎)
# 组员3：回测引擎开发
# 适配数据：沪深300ETF (sh.510300)
# ==================================================================

import pandas as pd
import numpy as np
import os
from dataclasses import dataclass


# ================= 第一部分：组员1的策略逻辑 =================
@dataclass(frozen=True)
class StrategyConfig:
    fast_window: int = 20
    slow_window: int = 60
    filter_window: int = 120
    price_col: str = "close"
    date_col: str = "date"


DEFAULT_CONFIG = StrategyConfig()


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
    sig = compute_indicators(df, config)
    n = len(sig)
    target_state = np.zeros(n, dtype=int)

    holding = 0
    for i in range(n):
        bullish = bool(sig["bullish"].iloc[i])
        above = bool(sig["above_filter"].iloc[i])
        ready = not (pd.isna(sig["ma_fast"].iloc[i]) or pd.isna(sig["ma_slow"].iloc[i]) or pd.isna(
            sig["ma_filter"].iloc[i]))

        if holding == 0:
            if ready and bullish and above:
                holding = 1
        else:
            if not bullish or not above:
                holding = 0
        target_state[i] = holding

    sig["target_state"] = target_state
    # 关键防未来函数：position 滞后一日
    sig["position"] = np.concatenate(([0], target_state[:-1]))

    # 标记买卖信号
    sig["trade"] = ""
    sig.loc[sig["position"].diff().fillna(0) > 0, "trade"] = "buy"
    sig.loc[sig["position"].diff().fillna(0) < 0, "trade"] = "sell"
    return sig


# ================= 第二部分：组员3的回测引擎 =================
class BacktestEngine:
    def __init__(self, initial_capital=1000000.0, commission_rate=0.00025, min_commission=5.0, stamp_duty_rate=0.001,
                 slippage=0.0001):
        """
        初始化回测引擎参数
        :param initial_capital: 初始资金 (默认100万)
        :param commission_rate: 佣金费率 (默认万分之2.5)
        :param min_commission: 最低佣金 (默认5元)
        :param stamp_duty_rate: 印花税 (默认千分之1，仅卖出收取)
        :param slippage: 滑点 (默认万分之1，模拟实盘摩擦)
        """
        self.initial_capital = initial_capital
        self.commission_rate = commission_rate
        self.min_commission = min_commission
        self.stamp_duty_rate = stamp_duty_rate
        self.slippage = slippage

    def run(self, df_signals):
        """核心回测执行逻辑"""
        cash = self.initial_capital
        shares = 0
        trades = []
        equity_records = []

        # 逐日遍历（事件驱动）
        for i in range(len(df_signals)):
            date = df_signals.loc[i, 'date']
            open_price = df_signals.loc[i, 'open']
            close_price = df_signals.loc[i, 'close']
            trade_signal = df_signals.loc[i, 'trade']

            # === 执行买入 ===
            if trade_signal == 'buy' and cash > 0:
                exec_price = open_price * (1 + self.slippage)
                # A股必须买100股的整数倍
                max_shares = int(cash / (exec_price * (1 + self.commission_rate)) // 100) * 100
                if max_shares > 0:
                    amount = max_shares * exec_price
                    commission = max(amount * self.commission_rate, self.min_commission)
                    if amount + commission <= cash:
                        cash -= (amount + commission)
                        shares += max_shares
                        trades.append(
                            {'日期': date, '动作': '买入', '成交价': round(exec_price, 4), '数量': max_shares})

            # === 执行卖出 ===
            elif trade_signal == 'sell' and shares > 0:
                exec_price = open_price * (1 - self.slippage)
                amount = shares * exec_price
                commission = max(amount * self.commission_rate, self.min_commission)
                stamp_duty = amount * self.stamp_duty_rate
                cash += (amount - commission - stamp_duty)
                trades.append({'日期': date, '动作': '卖出', '成交价': round(exec_price, 4), '数量': shares})
                shares = 0

            # === 每日盯市结算 ===
            total_asset = cash + shares * close_price
            equity_records.append({'date': date, 'total_asset': total_asset})

        return pd.DataFrame(equity_records), pd.DataFrame(trades)


# ================= 第三部分：主程序运行 =================
if __name__ == "__main__":
    print(">>> 1. 开始回测，正在读取数据...")

    # 指定数据文件（请确保文件已下载并放在同一目录）
    data_path = 'etf_510300_data.csv'
    TARGET_CODE = 'sh.510300'

    if not os.path.exists(data_path):
        print(f"❌ 错误：找不到数据文件 {data_path}")
        print("请先运行获取数据的代码，或者检查文件名是否正确！")
    else:
        # 读取数据
        df_raw = pd.read_csv(data_path)

        # 兼容处理：防止akshare导出的列名是中文
        if '日期' in df_raw.columns: df_raw = df_raw.rename(columns={'日期': 'date', '开盘': 'open', '收盘': 'close'})

        # 提取目标标的并清洗
        df_target = df_raw[df_raw['code'] == TARGET_CODE].copy()
        if df_target.empty and 'code' not in df_raw.columns:
            # 如果没有code列，说明整个文件就是我们要的数据
            df_target = df_raw.copy()

        df_target['date'] = pd.to_datetime(df_target['date'])
        df_target = df_target.sort_values('date').reset_index(drop=True)

        print(f">>> 2. 正在基于 {TARGET_CODE} 生成策略信号...")
        df_signals = generate_signals(df_target, DEFAULT_CONFIG)

        print(">>> 3. 启动回测引擎执行交易（含手续费、印花税、滑点）...")
        engine = BacktestEngine()
        df_equity, df_trades = engine.run(df_signals)

        print(">>> 4. 计算净值与基准对比...")
        # 策略净值
        df_equity['strategy_nav'] = df_equity['total_asset'] / engine.initial_capital
        # 基准净值（买入并持有）
        df_equity['benchmark_nav'] = df_signals['close'] / df_signals['close'].iloc[0]

        # 导出给组员4用的 CSV
        df_equity[['date', 'total_asset', 'strategy_nav', 'benchmark_nav']].to_csv('equity_curve.csv', index=False,
                                                                                   encoding='utf-8-sig')
        # 导出给组员5用的 CSV
        df_trades.to_csv('trade_log.csv', index=False, encoding='utf-8-sig')

        print("\n" + "=" * 40)
        print("🎉 回测完成！")
        print(f"策略期末净值: {df_equity['strategy_nav'].iloc[-1]:.4f}")
        print(f"基准期末净值: {df_equity['benchmark_nav'].iloc[-1]:.4f}")
        print(f"共发生交易笔数: {len(df_trades)}")
        print("结果已保存为: equity_curve.csv 和 trade_log.csv")
        print("=" * 40)