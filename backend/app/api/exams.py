"""
考试模块 API
提供考试生成、答题、批改和试卷导出功能
"""

import json
import logging
from flask import Blueprint, request, jsonify, render_template_string
from flask_login import login_required, current_user
from app.models.exam import Exam, ExamQuestion, ExamResult
from app.models.plan import LearningPlan, PlanItem
from app.models.content import LearningContent
from app.utils.llm_client import LLMClient

logger = logging.getLogger(__name__)

bp = Blueprint('exams', __name__, url_prefix='/api/exams')


@bp.route('/generate', methods=['POST'])
@login_required
def generate_exam():
    """根据plan_id和item_id生成考试"""
    data = request.get_json()
    plan_id = data.get('plan_id')
    item_id = data.get('item_id')
    num_questions = data.get('num_questions', 10)

    if not plan_id or not item_id:
        return jsonify({'error': '缺少plan_id或item_id参数'}), 400

    # 获取计划项目
    plan = LearningPlan.get_by_id(plan_id)
    item = PlanItem.get_by_id(item_id)
    if not plan or not item:
        return jsonify({'error': '计划或项目不存在'}), 404

    # 获取学习内容
    content = LearningContent.get_by_item(item_id)
    if not content:
        return jsonify({'error': '该学习项目还没有生成学习内容，请先学习'}), 400

    # 使用LLM生成题目
    topic = plan.topic or plan.title
    content_text = content.content_markdown or content.content_html or content.summary or ''

    llm = LLMClient()
    questions = llm.generate_exam_questions(topic, content_text, num_questions)

    if not questions:
        return jsonify({'error': '题目生成失败，请重试'}), 500

    # 创建考试
    exam = Exam.create(
        plan_id=plan_id,
        title=f'{item.title} - 考试',
        item_id=item_id,
        description=f'基于"{item.title}"学习内容的测试'
    )

    # 保存题目
    for q in questions:
        options_str = json.dumps(q.get('options', []), ensure_ascii=False) if q.get('options') else None
        exam.add_question(
            question_type=q.get('type', 'single_choice'),
            question=q.get('question', ''),
            correct_answer=q.get('correct_answer', ''),
            options=options_str,
            explanation=q.get('explanation', ''),
            difficulty=q.get('difficulty', 'medium')
        )

    # 重新获取考试（包含题目数量）
    exam = Exam.get_by_id(exam.id)

    return jsonify({
        'exam': {
            'id': exam.id,
            'plan_id': exam.plan_id,
            'item_id': exam.item_id,
            'title': exam.title,
            'description': exam.description,
            'total_questions': exam.total_questions,
            'passing_score': exam.passing_score,
            'created_at': str(exam.created_at)
        }
    })


@bp.route('/<int:exam_id>', methods=['GET'])
@login_required
def get_exam(exam_id):
    """获取考试详情（含题目但不包含答案）"""
    exam = Exam.get_by_id(exam_id)
    if not exam:
        return jsonify({'error': '考试不存在'}), 404

    questions = exam.get_questions()

    # 构建题目列表，不返回答案和解析
    question_list = []
    for q in questions:
        q_dict = {
            'id': q.id,
            'question_type': q.question_type,
            'question': q.question,
            'difficulty': q.difficulty
        }
        # 解析选项
        if q.options:
            try:
                q_dict['options'] = json.loads(q.options)
            except (json.JSONDecodeError, TypeError):
                q_dict['options'] = []
        else:
            q_dict['options'] = []

        # 判断题不需要选项，但需要显示"正确/错误"
        if q.question_type == 'true_false':
            q_dict['options'] = ['正确', '错误']

        question_list.append(q_dict)

    return jsonify({
        'exam': {
            'id': exam.id,
            'plan_id': exam.plan_id,
            'item_id': exam.item_id,
            'title': exam.title,
            'description': exam.description,
            'total_questions': exam.total_questions,
            'passing_score': exam.passing_score,
            'created_at': str(exam.created_at)
        },
        'questions': question_list
    })


@bp.route('/<int:exam_id>/submit', methods=['POST'])
@login_required
def submit_exam(exam_id):
    """提交答案并自动批改"""
    exam = Exam.get_by_id(exam_id)
    if not exam:
        return jsonify({'error': '考试不存在'}), 404

    data = request.get_json()
    answers = data.get('answers', {})

    if not answers:
        return jsonify({'error': '请提交答案'}), 400

    questions = exam.get_questions()

    # 批改
    correct_count = 0
    total_count = len(questions)
    results = []

    for q in questions:
        user_answer = answers.get(str(q.id), '')
        is_correct = False

        if q.question_type == 'single_choice':
            is_correct = user_answer.strip().upper() == q.correct_answer.strip().upper()
        elif q.question_type == 'multiple_choice':
            # 多选题：将答案排序后比较
            user_sorted = sorted([a.strip().upper() for a in user_answer.split(',')])
            correct_sorted = sorted([a.strip().upper() for a in q.correct_answer.split(',')])
            is_correct = user_sorted == correct_sorted
        elif q.question_type == 'true_false':
            is_correct = user_answer.strip() == q.correct_answer.strip()
        elif q.question_type == 'fill_blank':
            is_correct = user_answer.strip().lower() == q.correct_answer.strip().lower()
        elif q.question_type == 'short_answer':
            # 简答题：关键词匹配（简单实现）
            keywords = q.correct_answer.split(',')
            matched = sum(1 for kw in keywords if kw.strip() in user_answer)
            is_correct = matched >= max(1, len(keywords) * 0.5)

        if is_correct:
            correct_count += 1

        # 解析选项
        options_list = []
        if q.options:
            try:
                options_list = json.loads(q.options)
            except (json.JSONDecodeError, TypeError):
                options_list = []
        if q.question_type == 'true_false':
            options_list = ['正确', '错误']

        results.append({
            'question_id': q.id,
            'question_type': q.question_type,
            'question': q.question,
            'options': options_list,
            'user_answer': user_answer,
            'correct_answer': q.correct_answer,
            'is_correct': is_correct,
            'explanation': q.explanation or ''
        })

    score = int((correct_count / total_count) * 100) if total_count > 0 else 0

    # 保存考试结果
    answers_json = json.dumps(answers, ensure_ascii=False)
    exam_result = ExamResult.create(
        exam_id=exam_id,
        user_id=current_user.id,
        score=score,
        correct_count=correct_count,
        total_count=total_count,
        answers=answers_json
    )

    passed = score >= exam.passing_score

    return jsonify({
        'result': {
            'id': exam_result.id,
            'exam_id': exam_id,
            'score': score,
            'correct_count': correct_count,
            'total_count': total_count,
            'passed': passed,
            'passing_score': exam.passing_score,
            'completed_at': str(exam_result.completed_at)
        },
        'details': results
    })


@bp.route('/<int:exam_id>/export', methods=['GET'])
@login_required
def export_exam(exam_id):
    """导出试卷为标准HTML格式（适合A4打印）"""
    exam = Exam.get_by_id(exam_id)
    if not exam:
        return jsonify({'error': '考试不存在'}), 404

    questions = exam.get_questions()

    # 按题型分组
    type_map = {
        'single_choice': '选择题',
        'multiple_choice': '选择题',
        'true_false': '判断题',
        'fill_blank': '填空题',
        'short_answer': '简答题'
    }

    # 分组：选择题（单选+多选）、判断题、填空题、简答题
    groups = {
        '选择题': [],
        '判断题': [],
        '填空题': [],
        '简答题': []
    }

    for q in questions:
        group_name = type_map.get(q.question_type, '其他')
        options_list = []
        if q.options:
            try:
                options_list = json.loads(q.options)
            except (json.JSONDecodeError, TypeError):
                options_list = []
        if q.question_type == 'true_false':
            options_list = ['正确', '错误']

        groups.setdefault(group_name, []).append({
            'question': q.question,
            'options': options_list,
            'type': q.question_type
        })

    # 生成试卷HTML
    html = _generate_exam_html(exam, groups)

    return jsonify({'html': html})


def _generate_exam_html(exam, groups):
    """生成标准试卷格式HTML"""
    # 题号计数器
    question_counter = [0]

    def render_question(q, idx):
        question_counter[0] += 1
        num = question_counter[0]
        lines = [f'<div class="question-item">']
        lines.append(f'  <p class="question-text">{num}. {q["question"]}</p>')

        if q['type'] in ('single_choice', 'multiple_choice') and q['options']:
            prefix = 'A'
            for opt in q['options']:
                lines.append(
                    f'  <div class="option-item">'
                    f'    <span class="option-blank"></span> '
                    f'{prefix}. {opt}'
                    f'  </div>'
                )
                prefix = chr(ord(prefix) + 1)
        elif q['type'] == 'true_false':
            lines.append(
                f'  <div class="option-item">'
                f'    <span class="option-blank"></span> A. 正确'
                f'  </div>'
            )
            lines.append(
                f'  <div class="option-item">'
                f'    <span class="option-blank"></span> B. 错误'
                f'  </div>'
            )
        elif q['type'] == 'fill_blank':
            lines.append(f'  <div class="answer-blank">答：_______________________________</div>')
        elif q['type'] == 'short_answer':
            lines.append(f'  <div class="answer-area">')
            lines.append(f'    <p>答：</p>')
            for _ in range(4):
                lines.append(f'    <div class="answer-line"></div>')
            lines.append(f'  </div>')

        lines.append(f'</div>')
        return '\n'.join(lines)

    # 构建试卷内容
    sections = []
    section_num = 0
    for group_name, questions in groups.items():
        if not questions:
            continue
        section_num += 1
        chinese_num = ['一', '二', '三', '四', '五', '六', '七', '八', '九', '十']
        num_label = chinese_num[section_num - 1] if section_num <= len(chinese_num) else str(section_num)

        section_html = f'<div class="exam-section">'
        section_html += f'  <h2 class="section-title">{num_label}、{group_name}（共{len(questions)}题）</h2>'
        for q in questions:
            section_html += render_question(q, 0)
        section_html += f'</div>'
        sections.append(section_html)

    sections_str = '\n'.join(sections)

    html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{exam.title} - 试卷</title>
    <style>
        @page {{
            size: A4;
            margin: 2cm 1.5cm;
        }}
        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }}
        body {{
            font-family: "SimSun", "宋体", "Noto Serif SC", serif;
            font-size: 14px;
            line-height: 1.8;
            color: #000;
            background: #fff;
            padding: 0;
        }}
        @media screen {{
            body {{
                max-width: 210mm;
                margin: 0 auto;
                padding: 20px;
                background: #f0f0f0;
            }}
            .paper {{
                background: #fff;
                padding: 2cm 1.5cm;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                margin-bottom: 20px;
            }}
        }}
        @media print {{
            body {{
                padding: 0;
            }}
            .paper {{
                padding: 0;
                box-shadow: none;
            }}
            .no-print {{
                display: none !important;
            }}
        }}

        /* 试卷头部 */
        .exam-header {{
            text-align: center;
            border-bottom: 3px double #000;
            padding-bottom: 15px;
            margin-bottom: 20px;
        }}
        .exam-header h1 {{
            font-size: 22px;
            font-weight: bold;
            letter-spacing: 4px;
            margin-bottom: 5px;
        }}
        .exam-header .exam-subtitle {{
            font-size: 14px;
            color: #333;
        }}

        /* 考生信息栏 */
        .student-info {{
            display: flex;
            justify-content: space-between;
            border: 1px solid #000;
            padding: 10px 15px;
            margin-bottom: 20px;
            font-size: 14px;
        }}
        .student-info span {{
            display: inline-block;
        }}
        .student-info .info-blank {{
            display: inline-block;
            width: 120px;
            border-bottom: 1px solid #000;
            margin-left: 5px;
        }}

        /* 注意事项 */
        .exam-notice {{
            margin-bottom: 20px;
            padding: 10px 15px;
            border: 1px dashed #666;
            background: #fafafa;
        }}
        .exam-notice h3 {{
            font-size: 14px;
            margin-bottom: 5px;
        }}
        .exam-notice ol {{
            padding-left: 20px;
            font-size: 13px;
        }}
        .exam-notice li {{
            margin-bottom: 3px;
        }}

        /* 题目区域 */
        .exam-section {{
            margin-bottom: 25px;
        }}
        .section-title {{
            font-size: 16px;
            font-weight: bold;
            margin-bottom: 12px;
            padding-bottom: 5px;
            border-bottom: 1px solid #ccc;
        }}

        /* 题目 */
        .question-item {{
            margin-bottom: 15px;
        }}
        .question-text {{
            font-size: 14px;
            line-height: 1.8;
            margin-bottom: 5px;
        }}
        .option-item {{
            padding-left: 30px;
            font-size: 14px;
            line-height: 2;
        }}
        .option-blank {{
            display: inline-block;
            width: 18px;
            height: 18px;
            border: 1px solid #000;
            border-radius: 50%;
            margin-right: 8px;
            vertical-align: middle;
            text-align: center;
            line-height: 18px;
        }}

        /* 填空题 */
        .answer-blank {{
            padding-left: 30px;
            margin-top: 5px;
            font-size: 14px;
        }}

        /* 简答题 */
        .answer-area {{
            padding-left: 30px;
            margin-top: 5px;
        }}
        .answer-area p {{
            margin-bottom: 5px;
        }}
        .answer-line {{
            border-bottom: 1px solid #999;
            height: 30px;
            margin-bottom: 5px;
        }}

        /* 打印按钮 */
        .print-btn {{
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 10px 20px;
            background: #4A90D9;
            color: white;
            border: none;
            border-radius: 6px;
            font-size: 14px;
            cursor: pointer;
            z-index: 1000;
            box-shadow: 0 2px 8px rgba(0,0,0,0.2);
        }}
        .print-btn:hover {{
            background: #357ABD;
        }}
    </style>
</head>
<body>
    <button class="print-btn no-print" onclick="window.print()">打印试卷</button>
    <div class="paper">
        <!-- 试卷标题 -->
        <div class="exam-header">
            <h1>{exam.title}</h1>
            <div class="exam-subtitle">{exam.description or ""}</div>
        </div>

        <!-- 考生信息栏 -->
        <div class="student-info">
            <span>姓名：<span class="info-blank"></span></span>
            <span>学号：<span class="info-blank"></span></span>
            <span>班级：<span class="info-blank"></span></span>
            <span>得分：<span class="info-blank"></span></span>
        </div>

        <!-- 注意事项 -->
        <div class="exam-notice">
            <h3>注意事项：</h3>
            <ol>
                <li>本试卷共 {exam.total_questions} 题，满分 100 分，及格线 {exam.passing_score} 分。</li>
                <li>请仔细阅读每道题目，在指定位置作答。</li>
                <li>选择题请将答案填写在题号前的括号内。</li>
                <li>填空题请将答案直接填写在横线上。</li>
                <li>简答题请在答题区域内作答，注意条理清晰。</li>
                <li>考试时间：60 分钟。</li>
            </ol>
        </div>

        <!-- 题目内容 -->
        {sections_str}
    </div>
</body>
</html>'''
    return html
