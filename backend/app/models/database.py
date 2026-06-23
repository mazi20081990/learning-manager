import sqlite3
import os
from flask import g
from app import app

def get_db():
    """获取数据库连接"""
    if 'db' not in g:
        db_path = app.config['DATABASE_URL'].replace('sqlite:///', '')
        g.db = sqlite3.connect(db_path)
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(error):
    """关闭数据库连接"""
    if hasattr(g, 'db'):
        g.db.close()

def init_db():
    """初始化数据库表"""
    db_path = app.config['DATABASE_URL'].replace('sqlite:///', '')
    os.makedirs(os.path.dirname(db_path) if os.path.dirname(db_path) else '.', exist_ok=True)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 用户表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            nickname TEXT,
            real_name TEXT,
            age INTEGER,
            occupation TEXT,
            learning_goal TEXT,
            avatar TEXT,
            role TEXT DEFAULT 'user',
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 学习者表 - 支持一个账户下多人员管理
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS learners (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            avatar TEXT,
            age INTEGER,
            grade TEXT,
            relation TEXT DEFAULT 'self',
            learning_style TEXT DEFAULT 'visual',
            is_default INTEGER DEFAULT 0,
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')

    # 学习计划表 - 关联到学习者而非直接关联用户
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS learning_plans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            learner_id INTEGER,
            title TEXT NOT NULL,
            topic TEXT NOT NULL,
            description TEXT,
            total_days INTEGER NOT NULL,
            mode TEXT DEFAULT 'student',
            status TEXT DEFAULT 'active',
            progress REAL DEFAULT 0,
            start_date DATE,
            end_date DATE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (learner_id) REFERENCES learners (id)
        )
    ''')
    
    # 计划项目表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS plan_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            plan_id INTEGER NOT NULL,
            day_number INTEGER NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            difficulty TEXT DEFAULT 'medium',
            status TEXT DEFAULT 'pending',
            mastery_level INTEGER DEFAULT 0,
            completed_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (plan_id) REFERENCES learning_plans (id)
        )
    ''')
    
    # 学习内容表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS learning_contents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            plan_id INTEGER NOT NULL,
            item_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            content_html TEXT,
            content_markdown TEXT,
            summary TEXT,
            tags TEXT,
            images TEXT,
            refs TEXT,
            generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (plan_id) REFERENCES learning_plans (id),
            FOREIGN KEY (item_id) REFERENCES plan_items (id)
        )
    ''')
    
    # 考试表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS exams (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            plan_id INTEGER NOT NULL,
            item_id INTEGER,
            title TEXT NOT NULL,
            description TEXT,
            total_questions INTEGER DEFAULT 0,
            passing_score INTEGER DEFAULT 60,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (plan_id) REFERENCES learning_plans (id)
        )
    ''')
    
    # 考试题目表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS exam_questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            exam_id INTEGER NOT NULL,
            question_type TEXT NOT NULL,
            question TEXT NOT NULL,
            options TEXT,
            correct_answer TEXT NOT NULL,
            explanation TEXT,
            difficulty TEXT DEFAULT 'medium',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (exam_id) REFERENCES exams (id)
        )
    ''')
    
    # 考试结果表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS exam_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            exam_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            score INTEGER,
            correct_count INTEGER,
            total_count INTEGER,
            answers TEXT,
            completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (exam_id) REFERENCES exams (id),
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # 错题集表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS wrong_answers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            question_id INTEGER NOT NULL,
            user_answer TEXT,
            review_count INTEGER DEFAULT 0,
            last_reviewed TIMESTAMP,
            next_review_date DATE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (question_id) REFERENCES exam_questions (id)
        )
    ''')
    
    # 通知日志表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS notification_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            plan_id INTEGER,
            item_id INTEGER,
            user_id INTEGER NOT NULL,
            channel TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            content TEXT,
            sent_at TIMESTAMP,
            error_message TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 学习记录表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS learning_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            plan_id INTEGER NOT NULL,
            item_id INTEGER,
            action TEXT NOT NULL,
            duration INTEGER,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (plan_id) REFERENCES learning_plans (id)
        )
    ''')
    
    # 成就表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS achievements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            badge_name TEXT NOT NULL,
            badge_icon TEXT,
            description TEXT,
            earned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # 积分表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS points (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            points INTEGER DEFAULT 0,
            total_earned INTEGER DEFAULT 0,
            total_spent INTEGER DEFAULT 0,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # 图片表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS images (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            plan_id INTEGER NOT NULL,
            item_id INTEGER,
            filename TEXT NOT NULL,
            original_path TEXT,
            thumbnail_path TEXT,
            preview_path TEXT,
            file_size INTEGER,
            width INTEGER,
            height INTEGER,
            format TEXT,
            tags TEXT,
            description TEXT,
            is_auto_generated INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (plan_id) REFERENCES learning_plans (id)
        )
    ''')
    
    # 搜索额度使用记录表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS search_quota_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date DATE NOT NULL,
            used_count INTEGER DEFAULT 0,
            limit_count INTEGER DEFAULT 80,
            alerted INTEGER DEFAULT 0,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 创建默认管理员用户 - 使用werkzeug安全哈希
    from werkzeug.security import generate_password_hash
    admin_hash = generate_password_hash('admin123')
    cursor.execute('''
        INSERT OR IGNORE INTO users (id, username, password_hash, nickname, role)
        VALUES (1, 'admin', ?, '管理员', 'admin')
    ''', (admin_hash,))

    conn.commit()
    conn.close()

    # 执行数据库迁移
    run_migrations()

    app.logger.info('数据库初始化完成')


def run_migrations():
    """执行数据库迁移"""
    conn = sqlite3.connect('data/learning_manager.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # 检查并添加 learners 表
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='learners'")
    if not cursor.fetchone():
        cursor.execute('''
            CREATE TABLE learners (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                avatar TEXT,
                age INTEGER,
                grade TEXT,
                relation TEXT DEFAULT 'self',
                learning_style TEXT DEFAULT 'visual',
                is_default INTEGER DEFAULT 0,
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        app.logger.info('创建 learners 表')

    # 检查 learning_plans 表是否有 learner_id 列
    cursor.execute("PRAGMA table_info(learning_plans)")
    columns = [col['name'] for col in cursor.fetchall()]
    if 'learner_id' not in columns:
        cursor.execute('ALTER TABLE learning_plans ADD COLUMN learner_id INTEGER')
        app.logger.info('添加 learner_id 列到 learning_plans 表')

    # 检查 learning_contents 表是否有 refs 列（而不是 references）
    cursor.execute("PRAGMA table_info(learning_contents)")
    columns = [col['name'] for col in cursor.fetchall()]
    if 'refs' not in columns and 'references' in columns:
        # SQLite 不支持直接重命名列，需要创建新表
        cursor.execute('''
            CREATE TABLE learning_contents_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                plan_id INTEGER NOT NULL,
                item_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                content_html TEXT,
                content_markdown TEXT,
                summary TEXT,
                tags TEXT,
                images TEXT,
                refs TEXT,
                generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (plan_id) REFERENCES learning_plans (id),
                FOREIGN KEY (item_id) REFERENCES plan_items (id)
            )
        ''')
        cursor.execute('''
            INSERT INTO learning_contents_new (id, plan_id, item_id, title, content_html, content_markdown, summary, tags, images, refs, generated_at)
            SELECT id, plan_id, item_id, title, content_html, content_markdown, summary, tags, images, references, generated_at FROM learning_contents
        ''')
        cursor.execute('DROP TABLE learning_contents')
        cursor.execute('ALTER TABLE learning_contents_new RENAME TO learning_contents')
        app.logger.info('重命名 references 列为 refs')
    elif 'refs' not in columns:
        cursor.execute('ALTER TABLE learning_contents ADD COLUMN refs TEXT')
        app.logger.info('添加 refs 列到 learning_contents 表')

    conn.commit()
    conn.close()
    app.logger.info('数据库迁移完成')
