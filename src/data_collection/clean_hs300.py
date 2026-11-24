#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""数据清洗脚本（组员2 原始交付）
去重、转数值、剔除异常价、停牌前向填充，合并为 data_cleaned_final.csv。
运行：python src/data_collection/clean_hs300.py
"""

import pandas as pd

import glob

import os



print("开始执行数据清洗任务...")



# 1. 找到 data 文件夹下所有的个股文件（排除基准数据）

file_list = glob.glob("data/raw/*.csv")

file_list = [f for f in file_list if 'benchmark' not in f]



clean_data_list = []



# 2. 逐个文件进行清洗

for file in file_list:

    # 读取原始数据

    df = pd.read_csv(file)

    

    # 【清洗步骤一：剔除重复行】

    df = df.drop_duplicates(subset=['date', 'code'])

    

    # 【清洗步骤二：统一格式，将文本转为数字】

    # 原始数据里有的空字符串或者空格，先替换成空值

    df = df.replace(r'^\s*$', pd.NA, regex=True)

    

    # 强制把价格、成交量等列转为浮点数（float），无法转的变成空值

    numeric_cols = ['open', 'high', 'low', 'close', 'volume', 'amount', 'turn', 'pctChg']

    for col in numeric_cols:

        if col in df.columns:

            df[col] = pd.to_numeric(df[col], errors='coerce')

            

    # 【清洗步骤三：处理异常值】

    # 如果收盘价小于等于0，这绝对是脏数据，直接删掉这一行

    df = df[df['close'] > 0]

    

    # 【清洗步骤四：缺失值处理（针对停牌）】

    # 按日期排序，如果某天停牌没有数据，用前一天的数据填充（ffill）

    df['date'] = pd.to_datetime(df['date'])

    df = df.sort_values('date')

    df = df.ffill()

    

    clean_data_list.append(df)



# 3. 把清洗好的 300 个文件拼成一个大表

print("正在合并清洗后的数据...")

all_cleaned_data = pd.concat(clean_data_list, ignore_index=True)



# 4. 按日期和代码重新排个序，看起来更整齐

all_cleaned_data = all_cleaned_data.sort_values(by=['date', 'code'])



# 5. 保存为最终交付的清洗结果文件

output_file = "data/raw/data_cleaned_final.csv"

all_cleaned_data.to_csv(output_file, index=False, encoding="utf-8-sig")



print(f"数据清洗完成！共处理了 {len(file_list)} 只股票。")

print(f"清洗后的总数据行数为：{len(all_cleaned_data)} 行。")

print(f"最终文件已保存为：{output_file}")