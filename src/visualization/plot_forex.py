#!/usr/bin/env python3
"""
外汇牌价历史趋势图
- 绘制指定货币的买入价/卖出价随时间变化
- 支持多货币对比（可选）
"""

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime
from ..utils.db_utils import db
import pandas as pd

plt.rcParams["font.family"] = "WenQuanYi Micro Hei"
plt.rcParams["axes.unicode_minus"] = False

def plot_currency_trend(currency_name='美元', save_path=None):
    """
    绘制某一种货币的买入价和卖出价历史趋势
    """
    conn = db.conn
    query = """
        SELECT buy_rate, sell_rate, fetch_time 
        FROM dwd_forex_rates 
        WHERE currency_name = %s AND is_active = 1
        ORDER BY fetch_time ASC
    """
    df = pd.read_sql(query, conn, params=(currency_name,))
    
    if df.empty:
        print(f"❌ 没有找到 {currency_name} 的历史数据")
        return
    
    # 转换数据类型
    df['buy_rate'] = pd.to_numeric(df['buy_rate'], errors='coerce')
    df['sell_rate'] = pd.to_numeric(df['sell_rate'], errors='coerce')
    df['fetch_time'] = pd.to_datetime(df['fetch_time'])
    
    # 绘制折线图
    fig, ax = plt.subplots(figsize=(10, 5))
    
    ax.plot(df['fetch_time'], df['buy_rate'], marker='o', label='现汇买入价', linewidth=2)
    ax.plot(df['fetch_time'], df['sell_rate'], marker='s', label='现汇卖出价', linewidth=2)
    
    # 格式化x轴时间
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
    ax.xaxis.set_major_locator(mdates.HourLocator(interval=1))
    plt.xticks(rotation=45)
    
    ax.set_title(f'{currency_name} 汇率趋势', fontsize=14)
    ax.set_xlabel('时间')
    ax.set_ylabel('价格 (人民币)')
    ax.legend()
    ax.grid(True, linestyle='--', alpha=0.7)
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=150)
        print(f"✅ 图表已保存至 {save_path}")
    else:
        plt.show()

def plot_multi_currency(currencies=['美元', '欧元', '日元']):
    """
    绘制多种货币的买入价对比（每个货币一条线）
    """
    conn = db.conn
    all_data = []
    for curr in currencies:
        query = """
            SELECT buy_rate, fetch_time 
            FROM dwd_forex_rates 
            WHERE currency_name = %s AND is_active = 1
            ORDER BY fetch_time ASC
        """
        df = pd.read_sql(query, conn, params=(curr,))
        if not df.empty:
            df['currency'] = curr
            all_data.append(df)
    
    if not all_data:
        print("❌ 没有任何数据")
        return
    
    df_all = pd.concat(all_data, ignore_index=True)
    df_all['buy_rate'] = pd.to_numeric(df_all['buy_rate'], errors='coerce')
    df_all['fetch_time'] = pd.to_datetime(df_all['fetch_time'])
    
    fig, ax = plt.subplots(figsize=(12, 6))
    
    for curr in currencies:
        subset = df_all[df_all['currency'] == curr]
        if not subset.empty:
            ax.plot(subset['fetch_time'], subset['buy_rate'], marker='o', label=curr)
    
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
    ax.xaxis.set_major_locator(mdates.HourLocator(interval=1))
    plt.xticks(rotation=45)
    
    ax.set_title('多货币现汇买入价趋势对比', fontsize=14)
    ax.set_xlabel('时间')
    ax.set_ylabel('价格 (人民币)')
    ax.legend()
    ax.grid(True, linestyle='--', alpha=0.7)
    plt.tight_layout()
    plt.show()

if __name__ == '__main__':
    # 单一货币趋势图（默认美元）
    plot_currency_trend('日元', save_path='usd_trend.png')
    
    # 多货币对比图（可选，取消注释即可运行）
    # plot_multi_currency(['美元', '欧元', '日元'])
