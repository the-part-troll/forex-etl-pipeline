
#!/usr/bin/env python3
"""
外汇牌价ETL核心
- 增量写入（基于价格哈希）
- 保留历史快照（时间序列）
- 脏数据日志
"""

import hashlib
import json
from datetime import datetime
from typing import List, Dict, Optional
from loguru import logger
from ..utils.db_utils import db

class ForexETL:
    def __init__(self):
        self.conn = db.conn

    def compute_row_hash(self, record: Dict) -> str:
        """
        计算行哈希（仅基于价格字段，不含时间）
        用于判断价格是否变化
        """
        # 选取价格相关字段
        price_fields = ['buy_rate', 'sell_rate', 'central_parity']
        values = [str(record.get(f, '')) for f in price_fields]
        raw = '|'.join(values)
        return hashlib.md5(raw.encode('utf-8')).hexdigest()

    def get_latest_hash_by_currency(self, currency: str) -> Optional[str]:
        """获取该货币最新记录的哈希值"""
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT hash_key FROM dwd_forex_rates WHERE currency_name = %s AND is_active = 1 ORDER BY fetch_time DESC LIMIT 1",
            (currency,)
        )
        row = cursor.fetchone()
        return row[0] if row else None

    def insert_ods(self, html: str) -> str:
        """存入ODS层（原始HTML），返回ODS记录ID"""
        content_hash = hashlib.md5(html.encode('utf-8')).hexdigest()
        ods_id = f"ods_{datetime.now().strftime('%Y%m%d%H%M%S')}"

        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO ods_forex_raw (id, raw_html, content_hash, fetch_time, parse_status) VALUES (%s, %s, %s, NOW(), 1)",
            (ods_id, html, content_hash)
        )
        self.conn.commit()
        logger.debug(f"ODS写入成功: {ods_id}")
        return ods_id

    def insert_dwd(self, record: Dict, ods_id: str) -> bool:
        """存入DWD层（清洗后明细），如果价格已变化则插入"""
        currency = record['currency']
        new_hash = self.compute_row_hash(record)
        latest_hash = self.get_latest_hash_by_currency(currency)

        # 哈希一致 → 价格未变，跳过
        if latest_hash == new_hash:
            logger.debug(f"⏭️ 跳过 {currency}，价格未变化")
            return False

        # 价格已变化 → 插入新记录
        record_id = f"{currency}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO dwd_forex_rates (
                id, currency_name, buy_rate, sell_rate, cash_buy, cash_sell,
                central_parity, publish_date, publish_time, fetch_time, hash_key, is_active
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), %s, 1)
        """, (
            record_id,
            currency,
            record.get('buy_rate'),
            record.get('sell_rate'),
            record.get('cash_buy'),
            record.get('cash_sell'),
            record.get('central_parity'),
            record.get('publish_date'),
            record.get('publish_time'),
            new_hash
        ))
        self.conn.commit()
        logger.info(f"✅ 新增记录: {currency} (哈希: {new_hash[:8]}...)")
        return True

    def log_dirty_data(self, error_type: str, detail: str, snippet: str = ''):
        """记录脏数据"""
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO forex_dirty_log (error_type, error_detail, raw_snippet) VALUES (%s, %s, %s)",
            (error_type, detail, snippet[:500])
        )
        self.conn.commit()

    def run_etl(self, html: str, parsed_records: List[Dict]) -> Dict:
        """
        执行完整ETL流程
        返回: {'inserted': N, 'skipped': M, 'errors': K}
        """
        stats = {'inserted': 0, 'skipped': 0, 'errors': 0}

        # 1. 写入ODS
        ods_id = self.insert_ods(html)

        # 2. 处理每条记录
        for record in parsed_records:
            try:
                currency = record.get('currency')
                if not currency:
                    self.log_dirty_data('missing_currency', '货币名称为空', str(record))
                    stats['errors'] += 1
                    continue

                inserted = self.insert_dwd(record, ods_id)
                if inserted:
                    stats['inserted'] += 1
                else:
                    stats['skipped'] += 1

            except Exception as e:
                logger.error(f"处理记录失败: {e}, record={record}")
                self.log_dirty_data('etl_error', str(e), json.dumps(record, ensure_ascii=False))
                stats['errors'] += 1

        logger.info(f"ETL完成: 新增{stats['inserted']}, 跳过{stats['skipped']}, 错误{stats['errors']}")
        return stats
