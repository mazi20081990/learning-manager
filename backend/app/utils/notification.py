import os
import json
import requests
import logging
import hmac
import hashlib
import base64
import urllib.parse
from datetime import datetime
from typing import Optional, Dict

logger = logging.getLogger(__name__)

class NotificationManager:
    """推送通知管理器"""
    
    def __init__(self):
        # 钉钉配置
        self.dingtalk_webhook = os.getenv('DINGTALK_WEBHOOK', '')
        self.dingtalk_secret = os.getenv('DINGTALK_SECRET', '')
        
        # 微信公众号配置
        self.wechat_app_id = os.getenv('WECHAT_APP_ID', '')
        self.wechat_app_secret = os.getenv('WECHAT_APP_SECRET', '')
        self.wechat_template_id = os.getenv('WECHAT_TEMPLATE_ID', '')
        
        # Server酱配置
        self.serverchan_key = os.getenv('SERVERCHAN_KEY', '')
    
    def _generate_dingtalk_sign(self, timestamp: str) -> str:
        """生成钉钉签名"""
        if not self.dingtalk_secret:
            return ''
        
        string_to_sign = f'{timestamp}\n{self.dingtalk_secret}'
        hmac_code = hmac.new(
            self.dingtalk_secret.encode('utf-8'),
            string_to_sign.encode('utf-8'),
            digestmod=hashlib.sha256
        ).digest()
        sign = urllib.parse.quote_plus(base64.b64encode(hmac_code))
        return sign
    
    def send_dingtalk(self, message: str, title: Optional[str] = None) -> bool:
        """
        发送钉钉消息
        
        Args:
            message: 消息内容
            title: 消息标题
        
        Returns:
            是否发送成功
        """
        if not self.dingtalk_webhook:
            logger.warning('未配置钉钉Webhook')
            return False
        
        try:
            timestamp = str(round(datetime.now().timestamp() * 1000))
            sign = self._generate_dingtalk_sign(timestamp)
            
            # 构建Webhook URL
            webhook_url = self.dingtalk_webhook
            if sign:
                webhook_url += f'&timestamp={timestamp}&sign={sign}'
            
            # 构建消息内容
            if title:
                content = f"**{title}**\n\n{message}"
            else:
                content = message
            
            payload = {
                'msgtype': 'markdown',
                'markdown': {
                    'title': title or '学习管家通知',
                    'text': content
                }
            }
            
            response = requests.post(
                webhook_url,
                headers={'Content-Type': 'application/json'},
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('errcode') == 0:
                    logger.info('钉钉消息发送成功')
                    return True
                else:
                    logger.error(f'钉钉消息发送失败: {result}')
                    return False
            else:
                logger.error(f'钉钉请求失败: {response.status_code}')
                return False
                
        except Exception as e:
            logger.error(f'发送钉钉消息异常: {e}')
            return False
    
    def send_wechat(self, message: str, title: Optional[str] = None) -> bool:
        """
        发送微信公众号消息
        
        Args:
            message: 消息内容
            title: 消息标题
        
        Returns:
            是否发送成功
        """
        if not all([self.wechat_app_id, self.wechat_app_secret, self.wechat_template_id]):
            logger.warning('未配置微信公众号')
            return False
        
        try:
            # 获取access_token
            token_url = f'https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={self.wechat_app_id}&secret={self.wechat_app_secret}'
            token_response = requests.get(token_url, timeout=10)
            
            if token_response.status_code != 200:
                logger.error('获取微信access_token失败')
                return False
            
            token_data = token_response.json()
            access_token = token_data.get('access_token')
            
            if not access_token:
                logger.error('微信access_token为空')
                return False
            
            # 发送模板消息
            template_url = f'https://api.weixin.qq.com/cgi-bin/message/template/send?access_token={access_token}'
            
            payload = {
                'touser': '',  # 需要填充用户openid
                'template_id': self.wechat_template_id,
                'data': {
                    'first': {'value': title or '学习管家通知'},
                    'keyword1': {'value': message},
                    'keyword2': {'value': datetime.now().strftime('%Y-%m-%d %H:%M')}
                }
            }
            
            response = requests.post(
                template_url,
                headers={'Content-Type': 'application/json'},
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('errcode') == 0:
                    logger.info('微信公众号消息发送成功')
                    return True
                else:
                    logger.error(f'微信公众号消息发送失败: {result}')
                    return False
            else:
                logger.error(f'微信公众号请求失败: {response.status_code}')
                return False
                
        except Exception as e:
            logger.error(f'发送微信公众号消息异常: {e}')
            return False
    
    def send_serverchan(self, message: str, title: Optional[str] = None) -> bool:
        """
        发送Server酱消息
        
        Args:
            message: 消息内容
            title: 消息标题
        
        Returns:
            是否发送成功
        """
        if not self.serverchan_key:
            logger.warning('未配置Server酱')
            return False
        
        try:
            url = f'https://sctapi.ftqq.com/{self.serverchan_key}.send'
            
            payload = {
                'title': title or '学习管家通知',
                'desp': message
            }
            
            response = requests.post(
                url,
                data=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('code') == 0:
                    logger.info('Server酱消息发送成功')
                    return True
                else:
                    logger.error(f'Server酱消息发送失败: {result}')
                    return False
            else:
                logger.error(f'Server酱请求失败: {response.status_code}')
                return False
                
        except Exception as e:
            logger.error(f'发送Server酱消息异常: {e}')
            return False
    
    def send_learning_notification(self, user_id: int, plan_id: int, item_id: int,
                                   title: str, content_url: str, channel: str = 'dingtalk') -> bool:
        """
        发送学习通知
        
        Args:
            user_id: 用户ID
            plan_id: 计划ID
            item_id: 项目ID
            title: 学习标题
            content_url: 学习内容链接
            channel: 推送渠道
        
        Returns:
            是否发送成功
        """
        message = f"""📚 今日学习计划

**{title}**

点击链接开始学习：
{content_url}

---
掌握后请点击确认：
{content_url}/confirm

未掌握请点击重新学习：
{content_url}/retry
"""
        
        if channel == 'dingtalk':
            return self.send_dingtalk(message, title='今日学习计划')
        elif channel == 'wechat':
            return self.send_wechat(message, title='今日学习计划')
        elif channel == 'serverchan':
            return self.send_serverchan(message, title='今日学习计划')
        else:
            logger.warning(f'未知的推送渠道: {channel}')
            return False
    
    def send_reminder(self, message: str, title: Optional[str] = None) -> bool:
        """
        发送提醒消息（所有渠道）
        
        Args:
            message: 消息内容
            title: 消息标题
        
        Returns:
            是否发送成功
        """
        results = []
        
        # 尝试所有渠道
        if self.dingtalk_webhook:
            results.append(self.send_dingtalk(message, title))
        
        if all([self.wechat_app_id, self.wechat_app_secret]):
            results.append(self.send_wechat(message, title))
        
        if self.serverchan_key:
            results.append(self.send_serverchan(message, title))
        
        return any(results)
    
    def test_all_channels(self) -> Dict:
        """
        测试所有推送渠道
        
        Returns:
            测试结果字典
        """
        test_message = '这是一条测试消息，来自学习管家系统。'
        test_title = '推送测试'
        
        results = {
            'dingtalk': self.send_dingtalk(test_message, test_title),
            'wechat': self.send_wechat(test_message, test_title),
            'serverchan': self.send_serverchan(test_message, test_title)
        }
        
        return results
