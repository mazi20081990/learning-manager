from app.models.database import get_db
from datetime import datetime, timedelta

class LearningPlan:
    def __init__(self, id=None, user_id=None, learner_id=None, title=None, topic=None, description=None,
                 total_days=None, mode='student', status='active', progress=0,
                 start_date=None, end_date=None, created_at=None, updated_at=None):
        self.id = id
        self.user_id = user_id
        self.learner_id = learner_id
        self.title = title
        self.topic = topic
        self.description = description
        self.total_days = total_days
        self.mode = mode
        self.status = status
        self.progress = progress
        self.start_date = start_date
        self.end_date = end_date
        self.created_at = created_at
        self.updated_at = updated_at
    
    @staticmethod
    def get_by_id(plan_id):
        """根据ID获取学习计划"""
        db = get_db()
        row = db.execute('SELECT * FROM learning_plans WHERE id = ?', (plan_id,)).fetchone()
        if row:
            return LearningPlan(**dict(row))
        return None
    
    @staticmethod
    def get_by_user(user_id, status=None):
        """获取用户的所有学习计划"""
        db = get_db()
        if status:
            rows = db.execute(
                'SELECT * FROM learning_plans WHERE user_id = ? AND status = ? ORDER BY created_at DESC',
                (user_id, status)
            ).fetchall()
        else:
            rows = db.execute(
                'SELECT * FROM learning_plans WHERE user_id = ? ORDER BY created_at DESC',
                (user_id,)
            ).fetchall()
        return [LearningPlan(**dict(row)) for row in rows]

    @staticmethod
    def get_by_learner(learner_id, status=None):
        """获取学习者的所有学习计划"""
        db = get_db()
        if status:
            rows = db.execute(
                'SELECT * FROM learning_plans WHERE learner_id = ? AND status = ? ORDER BY created_at DESC',
                (learner_id, status)
            ).fetchall()
        else:
            rows = db.execute(
                'SELECT * FROM learning_plans WHERE learner_id = ? ORDER BY created_at DESC',
                (learner_id,)
            ).fetchall()
        return [LearningPlan(**dict(row)) for row in rows]
    
    @staticmethod
    def create(user_id, title, topic, total_days, mode='student', description=None, learner_id=None):
        """创建学习计划"""
        db = get_db()
        start_date = datetime.now().date()
        end_date = start_date + timedelta(days=total_days)

        cursor = db.execute(
            '''INSERT INTO learning_plans (user_id, learner_id, title, topic, description, total_days, mode, start_date, end_date)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
            (user_id, learner_id, title, topic, description, total_days, mode, start_date, end_date)
        )
        db.commit()
        return LearningPlan.get_by_id(cursor.lastrowid)
    
    def update(self, **kwargs):
        """更新学习计划"""
        db = get_db()
        fields = []
        values = []
        for key, value in kwargs.items():
            if hasattr(self, key):
                fields.append(f'{key} = ?')
                values.append(value)
        if fields:
            values.append(self.id)
            db.execute(
                f"UPDATE learning_plans SET {', '.join(fields)}, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                values
            )
            db.commit()
            for key, value in kwargs.items():
                setattr(self, key, value)
        return self
    
    def delete(self):
        """删除学习计划"""
        db = get_db()
        db.execute('DELETE FROM learning_plans WHERE id = ?', (self.id,))
        db.commit()
    
    def get_items(self):
        """获取计划的所有项目"""
        db = get_db()
        rows = db.execute(
            'SELECT * FROM plan_items WHERE plan_id = ? ORDER BY day_number',
            (self.id,)
        ).fetchall()
        return [PlanItem(**dict(row)) for row in rows]
    
    def get_current_item(self):
        """获取当前进行中的项目"""
        db = get_db()
        row = db.execute(
            '''SELECT * FROM plan_items 
               WHERE plan_id = ? AND status IN ('pending', 'in_progress')
               ORDER BY day_number LIMIT 1''',
            (self.id,)
        ).fetchone()
        if row:
            return PlanItem(**dict(row))
        return None
    
    def calculate_progress(self):
        """计算学习进度"""
        db = get_db()
        result = db.execute(
            '''SELECT 
               COUNT(*) as total,
               SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed
               FROM plan_items WHERE plan_id = ?''',
            (self.id,)
        ).fetchone()
        
        if result['total'] > 0:
            progress = (result['completed'] / result['total']) * 100
            self.update(progress=progress)
            return progress
        return 0
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'learner_id': self.learner_id,
            'title': self.title,
            'topic': self.topic,
            'description': self.description,
            'total_days': self.total_days,
            'mode': self.mode,
            'status': self.status,
            'progress': self.progress,
            'start_date': self.start_date,
            'end_date': self.end_date,
            'created_at': self.created_at
        }


class PlanItem:
    def __init__(self, id=None, plan_id=None, day_number=None, title=None,
                 description=None, difficulty='medium', status='pending',
                 mastery_level=0, completed_at=None, created_at=None):
        self.id = id
        self.plan_id = plan_id
        self.day_number = day_number
        self.title = title
        self.description = description
        self.difficulty = difficulty
        self.status = status
        self.mastery_level = mastery_level
        self.completed_at = completed_at
        self.created_at = created_at
    
    @staticmethod
    def get_by_id(item_id):
        """根据ID获取计划项目"""
        db = get_db()
        row = db.execute('SELECT * FROM plan_items WHERE id = ?', (item_id,)).fetchone()
        if row:
            return PlanItem(**dict(row))
        return None
    
    @staticmethod
    def create(plan_id, day_number, title, description=None, difficulty='medium'):
        """创建计划项目"""
        db = get_db()
        cursor = db.execute(
            '''INSERT INTO plan_items (plan_id, day_number, title, description, difficulty)
               VALUES (?, ?, ?, ?, ?)''',
            (plan_id, day_number, title, description, difficulty)
        )
        db.commit()
        return PlanItem.get_by_id(cursor.lastrowid)
    
    def update(self, **kwargs):
        """更新计划项目"""
        db = get_db()
        fields = []
        values = []
        for key, value in kwargs.items():
            if hasattr(self, key):
                fields.append(f'{key} = ?')
                values.append(value)
        if fields:
            values.append(self.id)
            db.execute(
                f"UPDATE plan_items SET {', '.join(fields)} WHERE id = ?",
                values
            )
            db.commit()
            for key, value in kwargs.items():
                setattr(self, key, value)
        return self
    
    def complete(self, mastery_level=None):
        """完成项目"""
        if mastery_level:
            self.update(status='completed', mastery_level=mastery_level, 
                       completed_at=datetime.now())
        else:
            self.update(status='completed', completed_at=datetime.now())
        
        # 更新计划进度
        plan = LearningPlan.get_by_id(self.plan_id)
        if plan:
            plan.calculate_progress()
        
        return self
    
    def get_content(self):
        """获取学习内容"""
        db = get_db()
        row = db.execute(
            'SELECT * FROM learning_contents WHERE item_id = ?',
            (self.id,)
        ).fetchone()
        if row:
            from app.models.content import LearningContent
            return LearningContent(**dict(row))
        return None
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'plan_id': self.plan_id,
            'day_number': self.day_number,
            'title': self.title,
            'description': self.description,
            'difficulty': self.difficulty,
            'status': self.status,
            'mastery_level': self.mastery_level,
            'completed_at': self.completed_at
        }
