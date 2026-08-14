#!/usr/bin/env python3
"""
中国银行外汇牌价爬虫
- 动态表头映射（列顺序自适应）
- 空值安全处理（不抛异常）
- 会话保持（Session复用）
"""

import requests
from bs4 import BeautifulSoup
from loguru import logger
import random
import time
from typing import List, Dict, Optional


class ForexCrawler:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        self.target_url = 'https://www.boc.cn/sourcedb/whpj/'
        self.timeout = 15

    def fetch_page(self, max_retries: int = 3) -> Optional[str]:
        """
        带重试的页面抓取（指数退避）
        """
        for attempt in range(1, max_retries + 1):
            try:
                # 请求前随机抖动（1~3秒）
                if attempt == 1:
                    jitter = random.uniform(1.0, 3.0)
                    logger.debug(f"⏳ 随机延迟 {jitter:.1f}s")
                    time.sleep(jitter)

                resp = self.session.get(self.target_url, timeout=self.timeout)
                resp.encoding = 'utf-8'

                if resp.status_code == 200:
                    logger.success(f"✅ 外汇页面抓取成功 (尝试 {attempt})")
                    return resp.text
                elif resp.status_code == 429:
                    wait = 60 * (2 ** (attempt - 1))  # 60s, 120s, 240s
                    logger.warning(f"⚠️ 触发限流(429)，等待 {wait}s 后重试...")
                    time.sleep(wait)
                else:
                    logger.warning(f"⚠️ 状态码 {resp.status_code} (尝试 {attempt})")
                    if attempt < max_retries:
                        time.sleep(random.uniform(5, 10))

            except requests.exceptions.RequestException as e:
                logger.warning(f"⚠️ 网络异常: {type(e).__name__} (尝试 {attempt})")
                if attempt < max_retries:
                    time.sleep(random.uniform(5, 10))

        logger.error(f"❌ 外汇页面抓取失败，已达最大重试次数 ({max_retries})")
        return None

    def parse_table(self, html: str) -> List[Dict]:
        """
        解析HTML表格（动态表头映射）
        通过查找包含"货币名称"的表头来定位正确的表格
        """
        soup = BeautifulSoup(html, 'html.parser')

        # 1. 定位数据表格：遍历所有 table，找到表头包含"货币名称"的
        target_table = None
        all_tables = soup.find_all('table')

        for table in all_tables:
            # 尝试从 thead 找表头
            thead = table.find('thead')
            if thead:
                header_row = thead.find('tr')
            else:
                # 降级：取第一个 tr 作为表头
                header_row = table.find('tr')

            if not header_row:
                continue

            # 提取表头文本
            header_cells = header_row.find_all(['th', 'td'])
            header_texts = [cell.get_text(strip=True) for cell in header_cells]

            # 检查是否包含"货币名称"关键词
            for text in header_texts:
                if '货币' in text or '币种' in text:
                    target_table = table
                    headers = header_texts
                    break

            if target_table:
                break

        if not target_table:
            logger.error("❌ 未找到包含'货币名称'的外汇牌价表格")
            return []

        # 2. 构建列名→索引映射
        column_map = {}
        for idx, name in enumerate(headers):
            if '货币' in name or '币种' in name:
                column_map['currency'] = idx
            elif '现汇买入' in name:
                column_map['buy_rate'] = idx
            elif '现钞买入' in name:
                column_map['cash_buy'] = idx
            elif '现汇卖出' in name:
                column_map['sell_rate'] = idx
            elif '现钞卖出' in name:
                column_map['cash_sell'] = idx
            elif '中行折算' in name or '折算价' in name:
                column_map['central_parity'] = idx
            elif '发布日' in name:
                column_map['publish_date'] = idx
            elif '发布时间' in name or '时间' in name:
                column_map['publish_time'] = idx

        # 必要字段检查
        required = ['currency', 'buy_rate', 'sell_rate']
        for field in required:
            if field not in column_map:
                logger.error(f"❌ 缺少必要字段映射: {field}, 实际表头: {headers}")
                return []

        # 3. 提取数据行（从 tbody 或第二行开始）
        tbody = target_table.find('tbody')
        rows = tbody.find_all('tr') if tbody else target_table.find_all('tr')[1:]

        results = []
        for row in rows:
            cells = row.find_all('td')
            if len(cells) < len(headers):
                continue  # 跳过异常行

            def safe_get(index: int) -> Optional[str]:
                if index is None or index >= len(cells):
                    return None
                text = cells[index].get_text(strip=True)
                return text if text and text != '-' else None

            record = {
                'currency': safe_get(column_map.get('currency')),
                'buy_rate': safe_get(column_map.get('buy_rate')),
                'cash_buy': safe_get(column_map.get('cash_buy')),
                'sell_rate': safe_get(column_map.get('sell_rate')),
                'cash_sell': safe_get(column_map.get('cash_sell')),
                'central_parity': safe_get(column_map.get('central_parity')),
                'publish_date': safe_get(column_map.get('publish_date')),
                'publish_time': safe_get(column_map.get('publish_time')),
            }

            if record['currency']:
                results.append(record)

        logger.info(f"✅ 解析完成，共 {len(results)} 种货币")
        return results
