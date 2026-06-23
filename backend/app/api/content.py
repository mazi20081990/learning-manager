from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from app.services.content_service import ContentService
from app.models.content import LearningContent
from app.models.plan import LearningPlan, PlanItem

bp = Blueprint('content', __name__, url_prefix='/api/content')
content_service = ContentService()

@bp.route('/<int:content_id>', methods=['GET'])
@login_required
def get_content(content_id):
    """获取学习内容"""
    content = content_service.get_content_with_images(content_id)
    if not content:
        return jsonify({'error': '内容不存在'}), 404
    
    # 检查权限
    plan = LearningPlan.get_by_id(content['plan_id'])
    if plan.user_id != current_user.id and not current_user.is_admin():
        return jsonify({'error': '无权访问'}), 403
    
    return jsonify({'content': content})

@bp.route('/item/<int:item_id>', methods=['GET'])
@login_required
def get_content_by_item(item_id):
    """根据项目ID获取学习内容"""
    item = PlanItem.get_by_id(item_id)
    if not item:
        return jsonify({'error': '项目不存在'}), 404
    
    plan = LearningPlan.get_by_id(item.plan_id)
    if plan.user_id != current_user.id and not current_user.is_admin():
        return jsonify({'error': '无权访问'}), 403
    
    content = content_service.get_content_by_item(item_id)
    if not content:
        return jsonify({'error': '内容不存在'}), 404
    
    content_with_images = content_service.get_content_with_images(content.id)
    return jsonify({'content': content_with_images})

@bp.route('/generate', methods=['POST'])
@login_required
def generate_content():
    """生成学习内容"""
    data = request.get_json()
    plan_id = data.get('plan_id')
    item_id = data.get('item_id')
    
    if not plan_id or not item_id:
        return jsonify({'error': '计划ID和项目ID不能为空'}), 400
    
    # 检查权限
    plan = LearningPlan.get_by_id(plan_id)
    if not plan:
        return jsonify({'error': '计划不存在'}), 404
    
    if plan.user_id != current_user.id and not current_user.is_admin():
        return jsonify({'error': '无权操作'}), 403
    
    # 生成内容
    content = content_service.generate_content(plan_id, item_id)
    if not content:
        return jsonify({'error': '内容生成失败'}), 500
    
    content_with_images = content_service.get_content_with_images(content.id)
    return jsonify({
        'message': '内容生成成功',
        'content': content_with_images
    })

@bp.route('/<int:content_id>/regenerate', methods=['POST'])
@login_required
def regenerate_content(content_id):
    """重新生成学习内容"""
    content = LearningContent.get_by_id(content_id)
    if not content:
        return jsonify({'error': '内容不存在'}), 404
    
    # 检查权限
    plan = LearningPlan.get_by_id(content.plan_id)
    if plan.user_id != current_user.id and not current_user.is_admin():
        return jsonify({'error': '无权操作'}), 403
    
    # 重新生成
    new_content = content_service.regenerate_content(content_id)
    if not new_content:
        return jsonify({'error': '内容重新生成失败'}), 500
    
    content_with_images = content_service.get_content_with_images(new_content.id)
    return jsonify({
        'message': '内容重新生成成功',
        'content': content_with_images
    })

@bp.route('/<int:content_id>/question', methods=['POST'])
@login_required
def ask_question(content_id):
    """提问"""
    data = request.get_json()
    question = data.get('question')
    
    if not question:
        return jsonify({'error': '问题不能为空'}), 400
    
    # 检查权限
    content = LearningContent.get_by_id(content_id)
    if not content:
        return jsonify({'error': '内容不存在'}), 404
    
    plan = LearningPlan.get_by_id(content.plan_id)
    if plan.user_id != current_user.id and not current_user.is_admin():
        return jsonify({'error': '无权访问'}), 403
    
    # 回答问题
    answer = content_service.answer_question(question, content_id)
    
    return jsonify({
        'question': question,
        'answer': answer
    })

@bp.route('/<int:content_id>', methods=['PUT'])
@login_required
def update_content(content_id):
    """更新学习内容"""
    content = LearningContent.get_by_id(content_id)
    if not content:
        return jsonify({'error': '内容不存在'}), 404
    
    # 检查权限
    plan = LearningPlan.get_by_id(content.plan_id)
    if plan.user_id != current_user.id and not current_user.is_admin():
        return jsonify({'error': '无权修改'}), 403
    
    data = request.get_json()
    content = content_service.update_content(content_id, **data)
    
    return jsonify({
        'message': '内容更新成功',
        'content': content.to_dict()
    })
