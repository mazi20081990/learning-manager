from app.models.database import get_db
from datetime import datetime

class Learner:
    """学习者模型 - 支持一个账户下多人员管理"""

    def __init__(self, id=None, user_id=None, name=None, avatar=None,
                 age=None, grade=None, relation=None, learning_style=None,
                 is_default=0, is_active=1, created_at=None, updated_at=None):
        self.id = id
        self.user_id = user_id
        self.name = name
        self.avatar = avatar
        self.age = age
        self.grade = grade
        self.relation = relation
        self.learning_style = learning_style
        self.is_default = is_default
        self.is_active = is_active
        self.created_at = created_at
        self.updated_at = updated_at

    @staticmethod
    def get_by_id(learner_id):
        """根据ID获取学习者"""
        db = get_db()
        row = db.execute('SELECT * FROM learners WHERE id = ?', (learner_id,)).fetchone()
        if row:
            return Learner(**dict(row))
        return None

    @staticmethod
    def get_by_user(user_id):
        """获取用户的所有学习者"""
        db = get_db()
        rows = db.execute(
            'SELECT * FROM learners WHERE user_id = ? AND is_active = 1 ORDER BY is_default DESC, created_at ASC',
            (user_id,)
        ).fetchall()
        return [Learner(**dict(row)) for row in rows]

    @staticmethod
    def get_default(user_id):
        """获取默认学习者"""
        db = get_db()
        row = db.execute(
            'SELECT * FROM learners WHERE user_id = ? AND is_default = 1 AND is_active = 1',
            (user_id,)
        ).fetchone()
        if row:
            return Learner(**dict(row))
        # 如果没有默认的，返回第一个
        rows = db.execute(
            'SELECT * FROM learners WHERE user_id = ? AND is_active = 1 ORDER BY created_at ASC LIMIT 1',
            (user_id,)
        ).fetchall()
        if rows:
            return Learner(**dict(rows[0]))
        return None

    @staticmethod
    def create(user_id, name, avatar=None, age=None, grade=None,
               relation='self', learning_style='visual', is_default=0):
        """创建学习者"""
        db = get_db()

        # 如果是第一个学习者，设为默认
        existing = db.execute('SELECT COUNT(*) as count FROM learners WHERE user_id = ?', (user_id,)).fetchone()
        if existing and existing['count'] == 0:
            is_default = 1

        cursor = db.execute(
            '''INSERT INTO learners (user_id, name, avatar, age, grade, relation, learning_style, is_default)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
            (user_id, name, avatar, age, grade, relation, learning_style, is_default)
        )
        db.commit()
        return Learner.get_by_id(cursor.lastrowid)

    def update(self, **kwargs):
        """更新学习者信息"""
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
                f"UPDATE learners SET {', '.join(fields)}, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                values
            )
            db.commit()
            for key, value in kwargs.items():
                setattr(self, key, value)
        return self

    def set_default(self):
        """设为默认学习者"""
        db = get_db()
        # 取消该用户下其他学习者的默认状态
        db.execute(
            'UPDATE learners SET is_default = 0 WHERE user_id = ?',
            (self.user_id,)
        )
        # 设置当前为默认
        db.execute(
            'UPDATE learners SET is_default = 1 WHERE id = ?',
            (self.id,)
        )
        db.commit()
        self.is_default = 1
        return self

    def delete(self):
        """删除学习者（软删除）"""
        db = get_db()
        db.execute('UPDATE learners SET is_active = 0 WHERE id = ?', (self.id,))
        db.commit()
        self.is_active = 0

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'name': self.name,
            'avatar': self.avatar,
            'age': self.age,
            'grade': self.grade,
            'relation': self.relation,
            'learning_style': self.learning_style,
            'is_default': self.is_default,
            'is_active': self.is_active
        }
