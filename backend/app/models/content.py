from app.models.database import get_db

class LearningContent:
    def __init__(self, id=None, plan_id=None, item_id=None, title=None,
                 content_html=None, content_markdown=None, summary=None,
                 tags=None, images=None, references=None, refs=None, generated_at=None):
        self.id = id
        self.plan_id = plan_id
        self.item_id = item_id
        self.title = title
        self.content_html = content_html
        self.content_markdown = content_markdown
        self.summary = summary
        self.tags = tags
        self.images = images
        # 数据库字段为refs，兼容references
        self.references = refs if refs is not None else references
        self.generated_at = generated_at
    
    @staticmethod
    def get_by_id(content_id):
        """根据ID获取学习内容"""
        db = get_db()
        row = db.execute('SELECT * FROM learning_contents WHERE id = ?', (content_id,)).fetchone()
        if row:
            return LearningContent(**dict(row))
        return None
    
    @staticmethod
    def get_by_item(item_id):
        """根据项目ID获取学习内容"""
        db = get_db()
        row = db.execute('SELECT * FROM learning_contents WHERE item_id = ?', (item_id,)).fetchone()
        if row:
            return LearningContent(**dict(row))
        return None
    
    @staticmethod
    def create(plan_id, item_id, title, content_html=None, content_markdown=None,
               summary=None, tags=None, images=None, refs=None):
        """创建学习内容"""
        db = get_db()
        cursor = db.execute(
            '''INSERT INTO learning_contents (plan_id, item_id, title, content_html,
               content_markdown, summary, tags, images, refs)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
            (plan_id, item_id, title, content_html, content_markdown,
             summary, tags, images, refs)
        )
        db.commit()
        return LearningContent.get_by_id(cursor.lastrowid)
    
    def update(self, **kwargs):
        """更新学习内容"""
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
                f"UPDATE learning_contents SET {', '.join(fields)} WHERE id = ?",
                values
            )
            db.commit()
            for key, value in kwargs.items():
                setattr(self, key, value)
        return self
    
    def delete(self):
        """删除学习内容"""
        db = get_db()
        db.execute('DELETE FROM learning_contents WHERE id = ?', (self.id,))
        db.commit()
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'plan_id': self.plan_id,
            'item_id': self.item_id,
            'title': self.title,
            'content_html': self.content_html,
            'content_markdown': self.content_markdown,
            'summary': self.summary,
            'tags': self.tags,
            'images': self.images,
            'references': self.references,
            'generated_at': self.generated_at
        }
