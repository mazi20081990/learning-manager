from app.models.database import get_db
from datetime import datetime

class NotificationLog:
    def __init__(self, id=None, plan_id=None, item_id=None, user_id=None,
                 channel=None, status='pending', content=None, sent_at=None,
                 error_message=None, created_at=None):
        self.id = id
        self.plan_id = plan_id
        self.item_id = item_id
        self.user_id = user_id
        self.channel = channel
        self.status = status
        self.content = content
        self.sent_at = sent_at
        self.error_message = error_message
        self.created_at = created_at
    
    @staticmethod
    def create(plan_id, user_id, channel, content, item_id=None):
        """创建通知日志"""
        db = get_db()
        cursor = db.execute(
            '''INSERT INTO notification_logs (plan_id, item_id, user_id, channel, content)
               VALUES (?, ?, ?, ?, ?)''',
            (plan_id, item_id, user_id, channel, content)
        )
        db.commit()
        return NotificationLog.get_by_id(cursor.lastrowid)
    
    @staticmethod
    def get_by_id(log_id):
        """根据ID获取通知日志"""
        db = get_db()
        row = db.execute('SELECT * FROM notification_logs WHERE id = ?', (log_id,)).fetchone()
        if row:
            return NotificationLog(**dict(row))
        return None
    
    @staticmethod
    def get_by_user(user_id, limit=50):
        """获取用户的通知日志"""
        db = get_db()
        rows = db.execute(
            'SELECT * FROM notification_logs WHERE user_id = ? ORDER BY created_at DESC LIMIT ?',
            (user_id, limit)
        ).fetchall()
        return [NotificationLog(**dict(row)) for row in rows]
    
    def mark_sent(self):
        """标记为已发送"""
        db = get_db()
        db.execute(
            'UPDATE notification_logs SET status = ?, sent_at = ? WHERE id = ?',
            ('sent', datetime.now(), self.id)
        )
        db.commit()
        self.status = 'sent'
        self.sent_at = datetime.now()
        return self
    
    def mark_failed(self, error_message):
        """标记为失败"""
        db = get_db()
        db.execute(
            'UPDATE notification_logs SET status = ?, error_message = ? WHERE id = ?',
            ('failed', error_message, self.id)
        )
        db.commit()
        self.status = 'failed'
        self.error_message = error_message
        return self
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'plan_id': self.plan_id,
            'item_id': self.item_id,
            'user_id': self.user_id,
            'channel': self.channel,
            'status': self.status,
            'content': self.content,
            'sent_at': self.sent_at,
            'error_message': self.error_message,
            'created_at': self.created_at
        }
