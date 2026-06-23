from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from app.models.learner import Learner
from app.models.plan import LearningPlan

bp = Blueprint('learners', __name__, url_prefix='/api/learners')

@bp.route('', methods=['GET', 'POST'])
@login_required
def handle_learners():
    """获取或创建学习者"""
    if request.method == 'GET':
        learners = Learner.get_by_user(current_user.id)
        return jsonify({
            'learners': [learner.to_dict() for learner in learners]
        })

    # POST - 创建学习者
    data = request.get_json()
    name = data.get('name')

    if not name:
        return jsonify({'error': '姓名不能为空'}), 400

    learner = Learner.create(
        user_id=current_user.id,
        name=name,
        avatar=data.get('avatar'),
        age=data.get('age'),
        grade=data.get('grade'),
        relation=data.get('relation', 'self'),
        learning_style=data.get('learning_style', 'visual'),
        is_default=data.get('is_default', 0)
    )

    return jsonify({
        'message': '学习者创建成功',
        'learner': learner.to_dict()
    }), 201

@bp.route('/<int:learner_id>', methods=['GET'])
@login_required
def get_learner(learner_id):
    """获取学习者详情"""
    learner = Learner.get_by_id(learner_id)
    if not learner:
        return jsonify({'error': '学习者不存在'}), 404

    if learner.user_id != current_user.id and not current_user.is_admin():
        return jsonify({'error': '无权访问'}), 403

    # 获取该学习者的学习计划
    plans = LearningPlan.get_by_learner(learner_id)

    return jsonify({
        'learner': learner.to_dict(),
        'plans': [plan.to_dict() for plan in plans]
    })

@bp.route('/<int:learner_id>', methods=['PUT'])
@login_required
def update_learner(learner_id):
    """更新学习者信息"""
    learner = Learner.get_by_id(learner_id)
    if not learner:
        return jsonify({'error': '学习者不存在'}), 404

    if learner.user_id != current_user.id and not current_user.is_admin():
        return jsonify({'error': '无权修改'}), 403

    data = request.get_json()
    learner.update(**data)

    return jsonify({
        'message': '学习者更新成功',
        'learner': learner.to_dict()
    })

@bp.route('/<int:learner_id>/default', methods=['POST'])
@login_required
def set_default_learner(learner_id):
    """设为默认学习者"""
    learner = Learner.get_by_id(learner_id)
    if not learner:
        return jsonify({'error': '学习者不存在'}), 404

    if learner.user_id != current_user.id and not current_user.is_admin():
        return jsonify({'error': '无权操作'}), 403

    learner.set_default()

    return jsonify({
        'message': '已设为默认学习者',
        'learner': learner.to_dict()
    })

@bp.route('/<int:learner_id>', methods=['DELETE'])
@login_required
def delete_learner(learner_id):
    """删除学习者"""
    learner = Learner.get_by_id(learner_id)
    if not learner:
        return jsonify({'error': '学习者不存在'}), 404

    if learner.user_id != current_user.id and not current_user.is_admin():
        return jsonify({'error': '无权删除'}), 403

    learner.delete()

    return jsonify({'message': '学习者已删除'})

@bp.route('/current', methods=['GET'])
@login_required
def get_current_learner():
    """获取当前默认学习者"""
    # 从session中获取当前选中的学习者
    from flask import session
    learner_id = session.get('current_learner_id')

    if learner_id:
        learner = Learner.get_by_id(learner_id)
        if learner and learner.user_id == current_user.id and learner.is_active:
            return jsonify({'learner': learner.to_dict()})

    # 返回默认学习者
    learner = Learner.get_default(current_user.id)
    if learner:
        return jsonify({'learner': learner.to_dict()})

    return jsonify({'learner': None})

@bp.route('/switch/<int:learner_id>', methods=['POST'])
@login_required
def switch_learner(learner_id):
    """切换当前学习者"""
    learner = Learner.get_by_id(learner_id)
    if not learner:
        return jsonify({'error': '学习者不存在'}), 404

    if learner.user_id != current_user.id and not current_user.is_admin():
        return jsonify({'error': '无权访问'}), 403

    if not learner.is_active:
        return jsonify({'error': '学习者已停用'}), 400

    # 保存到session
    from flask import session
    session['current_learner_id'] = learner_id

    return jsonify({
        'message': '切换成功',
        'learner': learner.to_dict()
    })
