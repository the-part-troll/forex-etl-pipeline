#!/usr/bin/env python3
"""
维基百科逝世人物列表爬虫
目标：抓取 2026年2月 逝世人物列表，解析出日期和人物描述
"""

import requests
from bs4 import BeautifulSoup
import re
from loguru import logger
import time
# 配置日志（输出到控制台）
logger.add(lambda msg: print(msg, end=""), format="{time} | {level} | {message}", level="INFO")


class WikiCrawler:

    def __init__(self, delay: float = 2.0):
        self.base_url = "https://wiki.gdrain.workers.dev"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        self.delay = delay  # 请求间隔（秒），避免触发反爬

    def fetch_monthly_page(self, month_key: str, max_retries: int = 3):
        """
        带重试机制的页面抓取
        - max_retries: 最大重试次数（包含首次请求）
        - 每次失败后等待 self.delay 秒
        """
        url = f"{self.base_url}/wiki/{month_key}逝世人物列表"

        for attempt in range(1, max_retries + 1):
            try:
                logger.info(f"抓取 {month_key} (尝试 {attempt}/{max_retries}): {url}")
                resp = requests.get(url, headers=self.headers, timeout=15)
                resp.encoding = 'utf-8'

                if resp.status_code == 200:
                    logger.success(f"✅ {month_key} 抓取成功 (尝试 {attempt})")
                    return resp.text
                else:
                    logger.warning(f"⚠️ {month_key} 状态码 {resp.status_code} (尝试 {attempt})")

            except requests.exceptions.RequestException as e:
                logger.warning(f"⚠️ {month_key} 网络异常: {type(e).__name__} (尝试 {attempt})")

            # 如果不是最后一次尝试，等待后继续
            if attempt < max_retries:
                logger.info(f"⏳ 等待 {self.delay} 秒后重试...")
                time.sleep(self.delay)

        logger.error(f"❌ {month_key} 抓取失败，已达到最大重试次数 ({max_retries})")
        return None

    def parse_entries(self, html: str):
        # import re  # <--- 移到这里
        soup = BeautifulSoup(html, 'html.parser')
        entries = []

        # 1. 定位所有包含日期文本的标题元素
        # 维基的日期标题通常在 class 为 'mw-heading' 的 div 或 h2/h3/h4 中
        date_headers = soup.select('h2.mw-heading, h3.mw-heading, h4.mw-heading, '
                                   '.mw-heading2, .mw-heading3, .mw-heading4')

        # 如果上面没找到，退而求其次：查找任何标题标签，文本匹配 "数字+日"
        if not date_headers:
            date_pattern = re.compile(r'^\s*(\d+)\s*日\s*$')
            date_headers = soup.find_all(['h2', 'h3', 'h4'])
            date_headers = [tag for tag in date_headers if date_pattern.match(tag.get_text(strip=True))]

        for header in date_headers:
            header_text = header.get_text(strip=True)
            # 找到该标题之后的第一个 <ul> 元素（不限层级）
            ul = header.find_next('ul')
            if ul:
                for li in ul.find_all('li', recursive=False):
                    raw_text = li.get_text(strip=True)
                    # 去除参考文献标记 [1] [2] ...
                    cleaned = re.sub(r'\[\d+\]', '', raw_text).strip()
                    if len(cleaned) > 5:
                        entries.append({
                            'date': header_text,
                            'raw_text': cleaned,
                            'source': 'wiki'
                        })
            else:
                # 调试信息
                print(f"⚠️ 日期标题 '{header_text}' 下未找到 ul 列表")

        return entries

    def crawl(self):
        """执行完整的爬取流程"""
        html = self.fetch_monthly_page()
        if not html:
            return []

        entries = self.parse_entries(html)
        logger.info(f"共解析到 {len(entries)} 个人物条目")
        return entries

    def crawl_months(self, months: list, max_retries_per_month: int = 3) -> dict:
        all_results = {}

        for month_key in months:
            # 每个月份独立重试（内部已经处理）
            html = self.fetch_monthly_page(month_key, max_retries=max_retries_per_month)
            if html:
                entries = self.parse_entries(html)
                all_results[month_key] = entries
                logger.success(f"✅ {month_key} 解析完成，共 {len(entries)} 条")
            else:
                all_results[month_key] = []
                logger.error(f"❌ {month_key} 最终失败，跳过该月份")

            # 月份之间的间隔（避免连续请求太密集）
            if month_key != months[-1]:
                logger.info(f"⏳ 等待 {self.delay} 秒后进入下个月份...")
                time.sleep(self.delay)

        return all_results


if __name__ == '__main__':
    # 你可以根据需要调整延迟和重试次数
    crawler = WikiCrawler(delay=10.0)  # 每次请求间隔2秒
    months = [f"2026年{i}月" for i in range(1, 9)]

    results = crawler.crawl_months(months, max_retries_per_month=3)

    # 统计
    total = 0
    for month, entries in results.items():
        print(f"{month}: {len(entries)} 条")
        total += len(entries)
    print(f"\n📊 总计: {total} 条人物记录")

    # 展示部分示例
    for month, entries in results.items():
        if entries:
            print(f"\n🔴 {month} 示例（前3条）：")
            for item in entries[:3]:
                print(f"  - {item['raw_text'][:60]}...")
            break  # 只展示第一个有数据的月份
