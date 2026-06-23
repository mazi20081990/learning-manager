from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app.models.database import get_db

class User(UserMixin):
    def __init__(self, id=None, username=None, password_hash=None, nickname=None,
                 real_name=None, age=None, occupation=None, learning_goal=None,
                 avatar=None, role='user', is_active=True, created_at=None, **kwargs):
        self.id = id
        self.username = username
        self.password_hash = password_hash
        self.nickname = nickname
        self.real_name = real_name
        self.age = age
        self.occupation = occupation
        self.learning_goal = learning_goal
        self.avatar = avatar
        self.role = role
        self._is_active = is_active

    @property
    def is_active(self):
        return self._is_active

    @is_active.setter
    def is_active(self, value):
        self._is_active = value
    
    def set_password(self, password):
        """设置密码"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """验证密码"""
        return check_password_hash(self.password_hash, password)
    
    def is_admin(self):
        """是否为管理员"""
        return self.role == 'admin'
    
    @staticmethod
    def get_by_id(user_id):
        """根据ID获取用户"""
        db = get_db()
        row = db.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
        if row:
            return User(**dict(row))
        return None
    
    @staticmethod
    def get_by_username(username):
        """根据用户名获取用户"""
        db = get_db()
        row = db.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        if row:
            return User(**dict(row))
        return None
    
    @staticmethod
    def create(username, password, nickname=None, real_name=None, age=None, 
               occupation=None, learning_goal=None, role='user'):
        """创建用户"""
        db = get_db()
        password_hash = generate_password_hash(password)
        cursor = db.execute(
            '''INSERT INTO users (username, password_hash, nickname, real_name, age, 
               occupation, learning_goal, role) 
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
            (username, password_hash, nickname, real_name, age, 
             occupation, learning_goal, role)
        )
        db.commit()
        return User.get_by_id(cursor.lastrowid)
    
    @staticmethod
    def get_all():
        """获取所有用户"""
        db = get_db()
        rows = db.execute('SELECT * FROM users ORDER BY created_at DESC').fetchall()
        return [User(**dict(row)) for row in rows]
    
    def update(self, **kwargs):
        """更新用户信息"""
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
                f"UPDATE users SET {', '.join(fields)}, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                values
            )
            db.commit()
            # 更新当前对象
            for key, value in kwargs.items():
                setattr(self, key, value)
        return self
    
    def delete(self):
        """删除用户"""
        db = get_db()
        db.execute('DELETE FROM users WHERE id = ?', (self.id,))
        db.commit()
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'username': self.username,
            'nickname': self.nickname,
            'real_name': self.real_name,
            'age': self.age,
            'occupation': self.occupation,
            'learning_goal': self.learning_goal,
            'avatar': self.avatar,
            'role': self.role,
            'is_active': self.is_active
        }
