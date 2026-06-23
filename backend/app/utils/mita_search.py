import os
import json
import requests
import logging
from datetime import datetime
from typing import List, Dict, Optional
from app.models.database import get_db

logger = logging.getLogger(__name__)

class MitaSearch:
    """秘塔搜索API客户端，支持额度管理"""
    
    def __init__(self):
        self.api_key = os.getenv('MITA_API_KEY', '')
        self.api_base = os.getenv('MITA_API_BASE', 'https://api.metaso.cn/v1')
        self.daily_limit = int(os.getenv('MITA_DAILY_LIMIT', '80'))
        self.alert_threshold = int(self.daily_limit * 0.8)  # 80%告警阈值
    
    def _get_today_usage(self) -> int:
        """获取今日使用量"""
        db = get_db()
        today = datetime.now().date()
        row = db.execute(
            'SELECT used_count FROM search_quota_logs WHERE date = ?',
            (today,)
        ).fetchone()
        return row['used_count'] if row else 0
    
    def _increment_usage(self):
        """增加使用量"""
        db = get_db()
        today = datetime.now().date()
        
        # 检查是否已存在记录
        row = db.execute(
            'SELECT id FROM search_quota_logs WHERE date = ?',
            (today,)
        ).fetchone()
        
        if row:
            db.execute(
                'UPDATE search_quota_logs SET used_count = used_count + 1, updated_at = CURRENT_TIMESTAMP WHERE date = ?',
                (today,)
            )
        else:
            db.execute(
                'INSERT INTO search_quota_logs (date, used_count, limit_count) VALUES (?, 1, ?)',
                (today, self.daily_limit)
            )
        db.commit()
    
    def _check_alert(self):
        """检查是否需要告警"""
        db = get_db()
        today = datetime.now().date()
        
        row = db.execute(
            'SELECT used_count, alerted FROM search_quota_logs WHERE date = ?',
            (today,)
        ).fetchone()
        
        if row and row['used_count'] >= self.alert_threshold and not row['alerted']:
            # 发送告警
            self._send_alert(row['used_count'])
            # 标记已告警
            db.execute(
                'UPDATE search_quota_logs SET alerted = 1 WHERE date = ?',
                (today,)
            )
            db.commit()
    
    def _send_alert(self, current_usage: int):
        """发送额度告警"""
        try:
            from app.utils.notification import NotificationManager
            notifier = NotificationManager()
            message = f"⚠️ 秘塔搜索额度告警\n\n今日已使用: {current_usage}/{self.daily_limit} 次\n剩余: {self.daily_limit - current_usage} 次\n\n请留意额度使用情况，避免超出限制。"
            notifier.send_dingtalk(message)
            logger.warning(f'秘塔搜索额度告警: {current_usage}/{self.daily_limit}')
        except Exception as e:
            logger.error(f'发送告警失败: {e}')
    
    def search(self, query: str, num_results: int = 5) -> List[Dict]:
        """
        搜索资料
        
        Args:
            query: 搜索关键词
            num_results: 返回结果数量
        
        Returns:
            搜索结果列表
        """
        # 检查额度
        current_usage = self._get_today_usage()
        if current_usage >= self.daily_limit:
            logger.warning(f'秘塔搜索额度已用完: {current_usage}/{self.daily_limit}')
            return []
        
        if not self.api_key:
            logger.error('未配置秘塔API Key')
            return []
        
        try:
            response = requests.post(
                f'{self.api_base}/search',
                headers={
                    'Authorization': f'Bearer {self.api_key}',
                    'Content-Type': 'application/json'
                },
                json={
                    'query': query,
                    'num_results': num_results,
                    'search_type': 'comprehensive'  # 综合搜索
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                
                # 增加使用量
                self._increment_usage()
                
                # 检查告警
                self._check_alert()
                
                # 解析结果
                search_results = []
                if 'results' in result:
                    for item in result['results']:
                        search_results.append({
                            'title': item.get('title', ''),
                            'summary': item.get('summary', ''),
                            'url': item.get('url', ''),
                            'source': item.get('source', ''),
                            'published_date': item.get('published_date', '')
                        })
                
                logger.info(f'秘塔搜索成功: {query}, 返回{len(search_results)}条结果')
                return search_results
            
            elif response.status_code == 429:
                logger.warning('秘塔搜索请求过于频繁')
                return []
            else:
                logger.error(f'秘塔搜索失败: {response.status_code} - {response.text}')
                return []
                
        except requests.exceptions.Timeout:
            logger.warning('秘塔搜索请求超时')
            return []
        except Exception as e:
            logger.error(f'秘塔搜索异常: {e}')
            return []
    
    def search_for_knowledge(self, topic: str, knowledge_point: str) -> List[Dict]:
        """
        为知识点搜索资料
        
        Args:
            topic: 学习主题
            knowledge_point: 知识点
        
        Returns:
            搜索结果列表
        """
        query = f"{topic} {knowledge_point} 教程 学习资料"
        return self.search(query, num_results=3)
    
    def get_quota_status(self) -> Dict:
        """
        获取额度状态
        
        Returns:
            额度状态字典
        """
        current_usage = self._get_today_usage()
        remaining = self.daily_limit - current_usage
        
        return {
            'daily_limit': self.daily_limit,
            'used_today': current_usage,
            'remaining': remaining,
            'usage_percentage': round((current_usage / self.daily_limit) * 100, 2),
            'alert_threshold': self.alert_threshold,
            'is_exceeded': current_usage >= self.daily_limit
        }
