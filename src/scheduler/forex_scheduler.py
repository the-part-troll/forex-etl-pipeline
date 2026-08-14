#!/usr/bin/env python3
"""
外汇牌价调度器
- 每5~6分钟运行一次（含随机抖动）
- 熔断机制：连续失败5次后暂停
- 日志全量记录
"""

import time
import random
from datetime import datetime
from loguru import logger
from ..collector.forex_crawler import ForexCrawler
from ..etl.forex_etl import ForexETL
from ..utils.db_utils import db

class ForexScheduler:
    def __init__(self):
        self.crawler = ForexCrawler()
        self.etl = ForexETL()
        self.fail_count = 0
        self.max_failures = 5
        self.base_interval = 300  # 5分钟
    
    def run_once(self) -> bool:
        """执行一次完整抓取+ETL，返回是否成功"""
        logger.info("=" * 60)
        logger.info(f"🔄 外汇牌价同步开始 @ {datetime.now()}")
        
        try:
            # 1. 抓取
            html = self.crawler.fetch_page()
            if not html:
                logger.error("❌ 抓取失败，本次同步终止")
                return False
            
            # 2. 解析
            records = self.crawler.parse_table(html)
            if not records:
                logger.warning("⚠️ 解析结果为空，可能页面结构变化")
                self.etl.log_dirty_data('parse_empty', '解析结果为空', html[:500])
                return False
            
            # 3. ETL
            stats = self.etl.run_etl(html, records)
            
            # 4. 重置失败计数
            self.fail_count = 0
            logger.success(f"✅ 同步成功: 新增{stats['inserted']}, 跳过{stats['skipped']}")
            return True
            
        except Exception as e:
            logger.error(f"❌ 同步异常: {e}")
            return False
    
    def run_forever(self):
        """主循环（含抖动和熔断）"""
        logger.info("🚀 外汇牌价调度器启动")
        
        while True:
            success = self.run_once()
            
            if not success:
                self.fail_count += 1
                logger.warning(f"⚠️ 连续失败 {self.fail_count}/{self.max_failures}")
                
                if self.fail_count >= self.max_failures:
                    logger.error("🔥 达到最大失败次数，调度器暂停，请手动检查网络和页面")
                    break
            else:
                self.fail_count = 0
            
            # 计算下一次运行间隔（5~7分钟随机）
            jitter = random.uniform(0, 120)  # 0~120秒随机
            next_interval = self.base_interval + jitter
            logger.info(f"⏳ 下次运行约 {next_interval/60:.1f} 分钟后")
            time.sleep(next_interval)


if __name__ == '__main__':
    scheduler = ForexScheduler()
    scheduler.run_forever()
