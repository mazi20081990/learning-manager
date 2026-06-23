from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from app.services.plan_service import PlanService
from app.models.plan import LearningPlan, PlanItem

bp = Blueprint('plans', __name__, url_prefix='/api/plans')
plan_service = PlanService()

@bp.route('', methods=['GET'])
@login_required
def get_plans():
    """获取学习计划列表"""
    status = request.args.get('status')
    learner_id = request.args.get('learner_id', type=int)

    # 如果指定了学习者ID，验证权限
    if learner_id:
        from app.models.learner import Learner
        learner = Learner.get_by_id(learner_id)
        if not learner or (learner.user_id != current_user.id and not current_user.is_admin()):
            return jsonify({'error': '无权访问该学习者的计划'}), 403

    plans = plan_service.get_user_plans(current_user.id, status, learner_id)
    return jsonify({
        'plans': [plan.to_dict() for plan in plans]
    })

@bp.route('/<int:plan_id>', methods=['GET'])
@login_required
def get_plan(plan_id):
    """获取学习计划详情"""
    plan = plan_service.get_plan(plan_id)
    if not plan:
        return jsonify({'error': '计划不存在'}), 404
    
    if plan.user_id != current_user.id and not current_user.is_admin():
        return jsonify({'error': '无权访问'}), 403
    
    items = plan.get_items()
    progress = plan_service.get_plan_progress(plan_id)
    
    return jsonify({
        'plan': plan.to_dict(),
        'items': [item.to_dict() for item in items],
        'progress': progress
    })

@bp.route('', methods=['POST'])
@login_required
def create_plan():
    """创建学习计划"""
    data = request.get_json()
    topic = data.get('topic')
    days = data.get('days')
    mode = data.get('mode', 'student')
    description = data.get('description')
    learner_id = data.get('learner_id')

    if not topic:
        return jsonify({'error': '主题不能为空'}), 400

    try:
        days = int(days)
    except (ValueError, TypeError):
        return jsonify({'error': '天数必须是有效的数字'}), 400

    if days < 1 or days > 365:
        return jsonify({'error': '天数必须在1-365之间'}), 400

    # 如果指定了学习者ID，验证权限
    if learner_id:
        from app.models.learner import Learner
        learner = Learner.get_by_id(learner_id)
        if not learner or (learner.user_id != current_user.id and not current_user.is_admin()):
            return jsonify({'error': '无权为该学习者创建计划'}), 403

    plan = plan_service.create_plan(
        user_id=current_user.id,
        topic=topic,
        days=days,
        mode=mode,
        description=description,
        learner_id=learner_id
    )
    print(f'[DEBUG] plan_service.create_plan returned: {plan}', flush=True)

    # 如果plan_service创建失败，直接使用模板创建
    if not plan:
        from app.models.plan import LearningPlan, PlanItem
        items_data = []
        for i in range(1, days + 1):
            items_data.append({
                'day_number': i,
                'title': f'{topic} - 第{i}天',
                'description': f'{topic}学习第{i}天的内容',
                'difficulty': 'easy' if i <= days // 3 else ('medium' if i <= 2 * days // 3 else 'hard')
            })
        plan = LearningPlan.create(
            user_id=current_user.id,
            learner_id=learner_id,
            title=f'{topic}{days}天学习计划',
            topic=topic,
            total_days=days,
            mode=mode,
            description=description or f'系统学习{topic}，共{days}天'
        )
        if plan:
            for item_data in items_data:
                PlanItem.create(
                    plan_id=plan.id,
                    day_number=item_data['day_number'],
                    title=item_data['title'],
                    description=item_data['description'],
                    difficulty=item_data['difficulty']
                )

    if not plan:
        return jsonify({'error': '创建计划失败'}), 500

    # 在后台预生成学习内容
    import threading
    threading.Thread(target=plan_service.batch_generate_content, args=(plan.id,), daemon=True).start()

    items = plan.get_items()
    return jsonify({
        'message': '计划创建成功',
        'plan': plan.to_dict(),
        'items': [item.to_dict() for item in items]
    }), 201

@bp.route('/<int:plan_id>', methods=['PUT'])
@login_required
def update_plan(plan_id):
    """更新学习计划"""
    plan = plan_service.get_plan(plan_id)
    if not plan:
        return jsonify({'error': '计划不存在'}), 404
    
    if plan.user_id != current_user.id and not current_user.is_admin():
        return jsonify({'error': '无权修改'}), 403
    
    data = request.get_json()
    plan = plan_service.update_plan(plan_id, **data)
    
    return jsonify({
        'message': '计划更新成功',
        'plan': plan.to_dict()
    })

@bp.route('/<int:plan_id>', methods=['DELETE'])
@login_required
def delete_plan(plan_id):
    """删除学习计划"""
    plan = plan_service.get_plan(plan_id)
    if not plan:
        return jsonify({'error': '计划不存在'}), 404
    
    if plan.user_id != current_user.id and not current_user.is_admin():
        return jsonify({'error': '无权删除'}), 403
    
    plan_service.delete_plan(plan_id)
    return jsonify({'message': '计划删除成功'})

@bp.route('/<int:plan_id>/items', methods=['POST'])
@login_required
def add_plan_item(plan_id):
    """添加计划项目"""
    plan = plan_service.get_plan(plan_id)
    if not plan:
        return jsonify({'error': '计划不存在'}), 404
    
    if plan.user_id != current_user.id and not current_user.is_admin():
        return jsonify({'error': '无权修改'}), 403
    
    data = request.get_json()
    day_number = data.get('day_number')
    title = data.get('title')
    description = data.get('description')
    difficulty = data.get('difficulty', 'medium')
    
    if not day_number or not title:
        return jsonify({'error': '天数和标题不能为空'}), 400
    
    item = plan_service.add_plan_item(plan_id, day_number, title, description, difficulty)
    
    return jsonify({
        'message': '项目添加成功',
        'item': item.to_dict()
    }), 201

@bp.route('/items/<int:item_id>', methods=['PUT'])
@login_required
def update_plan_item(item_id):
    """更新计划项目"""
    item = PlanItem.get_by_id(item_id)
    if not item:
        return jsonify({'error': '项目不存在'}), 404
    
    plan = plan_service.get_plan(item.plan_id)
    if plan.user_id != current_user.id and not current_user.is_admin():
        return jsonify({'error': '无权修改'}), 403
    
    data = request.get_json()
    item = plan_service.update_plan_item(item_id, **data)
    
    return jsonify({
        'message': '项目更新成功',
        'item': item.to_dict()
    })

@bp.route('/items/<int:item_id>', methods=['DELETE'])
@login_required
def delete_plan_item(item_id):
    """删除计划项目"""
    item = PlanItem.get_by_id(item_id)
    if not item:
        return jsonify({'error': '项目不存在'}), 404
    
    plan = plan_service.get_plan(item.plan_id)
    if plan.user_id != current_user.id and not current_user.is_admin():
        return jsonify({'error': '无权删除'}), 403
    
    plan_service.delete_plan_item(item_id)
    return jsonify({'message': '项目删除成功'})

@bp.route('/items/<int:item_id>/complete', methods=['POST'])
@login_required
def complete_item(item_id):
    """完成计划项目"""
    item = PlanItem.get_by_id(item_id)
    if not item:
        return jsonify({'error': '项目不存在'}), 404
    
    plan = plan_service.get_plan(item.plan_id)
    if plan.user_id != current_user.id and not current_user.is_admin():
        return jsonify({'error': '无权操作'}), 403
    
    data = request.get_json() or {}
    mastery_level = data.get('mastery_level')
    
    item = plan_service.complete_item(item_id, mastery_level)
    
    return jsonify({
        'message': '项目完成',
        'item': item.to_dict()
    })

@bp.route('/recommend-days', methods=['POST'])
@login_required
def recommend_days():
    """根据主题推荐学习天数"""
    data = request.get_json()
    topic = data.get('topic', '')
    if not topic:
        return jsonify({'days': 7})
    days = plan_service.recommend_days(topic)
    return jsonify({'days': days})

@bp.route('/templates', methods=['GET'])
@login_required
def get_templates():
    """获取预设模板"""
    templates = plan_service.get_templates()
    return jsonify({'templates': templates})

@bp.route('/<int:plan_id>/pause', methods=['POST'])
@login_required
def pause_plan(plan_id):
    """暂停学习计划"""
    plan = plan_service.get_plan(plan_id)
    if not plan:
        return jsonify({'error': '计划不存在'}), 404
    
    if plan.user_id != current_user.id and not current_user.is_admin():
        return jsonify({'error': '无权操作'}), 403
    
    plan = plan_service.pause_plan(plan_id)
    return jsonify({
        'message': '计划已暂停',
        'plan': plan.to_dict()
    })

@bp.route('/<int:plan_id>/resume', methods=['POST'])
@login_required
def resume_plan(plan_id):
    """恢复学习计划"""
    plan = plan_service.get_plan(plan_id)
    if not plan:
        return jsonify({'error': '计划不存在'}), 404
    
    if plan.user_id != current_user.id and not current_user.is_admin():
        return jsonify({'error': '无权操作'}), 403
    
    plan = plan_service.resume_plan(plan_id)
    return jsonify({
        'message': '计划已恢复',
        'plan': plan.to_dict()
    })
