#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""数据采集脚本（组员2 原始交付）
用 baostock 下载沪深300成分股 2018-2023 日线数据。
运行：python src/data_collection/download_hs300.py
注意：需联网，且只用于数据探索/后续多因子扩展，不参与主回测。
"""

import baostock as bs

import pandas as pd

import os

import time



lg = bs.login()



if not os.path.exists("data"):

    os.makedirs("data")



print("正在获取沪深300成分股名单...")

rs = bs.query_hs300_stocks()

hs300_stocks = []

while (rs.error_code == '0') & rs.next():

    hs300_stocks.append(rs.get_row_data())



df_hs300 = pd.DataFrame(hs300_stocks, columns=rs.fields)

stock_codes = df_hs300['code'].tolist() 



print(f"共获取到 {len(stock_codes)} 只股票，准备开始下载...")



for i, code in enumerate(stock_codes):

    file_name = code.split('.')[1] + '.csv'

    file_path = f"data/raw/{file_name}"

    

    # 🌟 核心：如果文件已经存在，直接跳过

    if os.path.exists(file_path):

        continue

        

    print(f"正在下载第 {i+1}/{len(stock_codes)} 只股票：{code}")

    

    rs_data = bs.query_history_k_data_plus(

        code,

        "date,code,open,high,low,close,volume,amount,turn,pctChg",

        start_date='2018-01-01', 

        end_date='2023-12-31',

        frequency="d", 

        adjustflag="2" 

    )

    

    data_list = []

    while (rs_data.error_code == '0') & rs_data.next():

        data_list.append(rs_data.get_row_data())

        

    if data_list:

        df = pd.DataFrame(data_list, columns=rs_data.fields)

        df = df.replace('', pd.NA)

        df.to_csv(file_path, index=False, encoding="utf-8-sig")

    

    time.sleep(0.1) 



# 顺便检查一下基准数据下没下

benchmark_path = "data/raw/benchmark_hs300.csv"

if not os.path.exists(benchmark_path):

    print("正在下载基准指数（沪深300）数据...")

    rs_index = bs.query_history_k_data_plus(

        "sh.000300",

        "date,code,open,high,low,close,volume,amount",

        start_date='2018-01-01', 

        end_date='2023-12-31',

        frequency="d", 

        adjustflag="3"

    )

    index_list = []

    while (rs_index.error_code == '0') & rs_index.next():

        index_list.append(rs_index.get_row_data())

    df_index = pd.DataFrame(index_list, columns=rs_index.fields)

    df_index.to_csv(benchmark_path, index=False, encoding="utf-8-sig")

    print("基准数据下载完毕！")



print("🎉 所有数据下载完毕！请查看 data 文件夹。")

bs.logout() 