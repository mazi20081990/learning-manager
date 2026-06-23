from app.models.database import get_db

class Exam:
    def __init__(self, id=None, plan_id=None, item_id=None, title=None,
                 description=None, total_questions=0, passing_score=60, created_at=None):
        self.id = id
        self.plan_id = plan_id
        self.item_id = item_id
        self.title = title
        self.description = description
        self.total_questions = total_questions
        self.passing_score = passing_score
        self.created_at = created_at
    
    @staticmethod
    def get_by_id(exam_id):
        """根据ID获取考试"""
        db = get_db()
        row = db.execute('SELECT * FROM exams WHERE id = ?', (exam_id,)).fetchone()
        if row:
            return Exam(**dict(row))
        return None
    
    @staticmethod
    def create(plan_id, title, item_id=None, description=None, passing_score=60):
        """创建考试"""
        db = get_db()
        cursor = db.execute(
            '''INSERT INTO exams (plan_id, item_id, title, description, passing_score)
               VALUES (?, ?, ?, ?, ?)''',
            (plan_id, item_id, title, description, passing_score)
        )
        db.commit()
        return Exam.get_by_id(cursor.lastrowid)
    
    def get_questions(self):
        """获取所有题目"""
        db = get_db()
        rows = db.execute(
            'SELECT * FROM exam_questions WHERE exam_id = ?',
            (self.id,)
        ).fetchall()
        return [ExamQuestion(**dict(row)) for row in rows]
    
    def add_question(self, question_type, question, correct_answer, 
                     options=None, explanation=None, difficulty='medium'):
        """添加题目"""
        return ExamQuestion.create(
            self.id, question_type, question, correct_answer,
            options, explanation, difficulty
        )


class ExamQuestion:
    def __init__(self, id=None, exam_id=None, question_type=None, question=None,
                 options=None, correct_answer=None, explanation=None, 
                 difficulty='medium', created_at=None):
        self.id = id
        self.exam_id = exam_id
        self.question_type = question_type
        self.question = question
        self.options = options
        self.correct_answer = correct_answer
        self.explanation = explanation
        self.difficulty = difficulty
        self.created_at = created_at
    
    @staticmethod
    def get_by_id(question_id):
        """根据ID获取题目"""
        db = get_db()
        row = db.execute('SELECT * FROM exam_questions WHERE id = ?', (question_id,)).fetchone()
        if row:
            return ExamQuestion(**dict(row))
        return None
    
    @staticmethod
    def create(exam_id, question_type, question, correct_answer,
               options=None, explanation=None, difficulty='medium'):
        """创建题目"""
        db = get_db()
        cursor = db.execute(
            '''INSERT INTO exam_questions (exam_id, question_type, question, options, 
               correct_answer, explanation, difficulty)
               VALUES (?, ?, ?, ?, ?, ?, ?)''',
            (exam_id, question_type, question, options, 
             correct_answer, explanation, difficulty)
        )
        db.commit()
        
        # 更新考试题目数量
        db.execute(
            'UPDATE exams SET total_questions = total_questions + 1 WHERE id = ?',
            (exam_id,)
        )
        db.commit()
        
        return ExamQuestion.get_by_id(cursor.lastrowid)


class ExamResult:
    def __init__(self, id=None, exam_id=None, user_id=None, score=None,
                 correct_count=None, total_count=None, answers=None, completed_at=None):
        self.id = id
        self.exam_id = exam_id
        self.user_id = user_id
        self.score = score
        self.correct_count = correct_count
        self.total_count = total_count
        self.answers = answers
        self.completed_at = completed_at
    
    @staticmethod
    def create(exam_id, user_id, score, correct_count, total_count, answers):
        """创建考试结果"""
        db = get_db()
        cursor = db.execute(
            '''INSERT INTO exam_results (exam_id, user_id, score, correct_count, 
               total_count, answers)
               VALUES (?, ?, ?, ?, ?, ?)''',
            (exam_id, user_id, score, correct_count, total_count, answers)
        )
        db.commit()
        return ExamResult.get_by_id(cursor.lastrowid)
    
    @staticmethod
    def get_by_id(result_id):
        """根据ID获取考试结果"""
        db = get_db()
        row = db.execute('SELECT * FROM exam_results WHERE id = ?', (result_id,)).fetchone()
        if row:
            return ExamResult(**dict(row))
        return None
    
    @staticmethod
    def get_by_user_and_exam(user_id, exam_id):
        """获取用户的考试结果"""
        db = get_db()
        rows = db.execute(
            'SELECT * FROM exam_results WHERE user_id = ? AND exam_id = ? ORDER BY completed_at DESC',
            (user_id, exam_id)
        ).fetchall()
        return [ExamResult(**dict(row)) for row in rows]
