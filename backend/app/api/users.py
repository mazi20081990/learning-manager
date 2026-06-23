from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash
from app.models.user import User

bp = Blueprint('users', __name__, url_prefix='/api/users')

@bp.route('', methods=['GET'])
@login_required
def get_users():
    """获取用户列表（仅管理员）"""
    if not current_user.is_admin():
        return jsonify({'error': '无权访问'}), 403
    
    users = User.get_all()
    return jsonify({
        'users': [user.to_dict() for user in users]
    })

@bp.route('/<int:user_id>', methods=['GET'])
@login_required
def get_user(user_id):
    """获取用户信息"""
    if current_user.id != user_id and not current_user.is_admin():
        return jsonify({'error': '无权访问'}), 403
    
    user = User.get_by_id(user_id)
    if not user:
        return jsonify({'error': '用户不存在'}), 404
    
    return jsonify({'user': user.to_dict()})

@bp.route('', methods=['POST'])
@login_required
def create_user():
    """创建用户（仅管理员）"""
    if not current_user.is_admin():
        return jsonify({'error': '无权操作'}), 403
    
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    nickname = data.get('nickname')
    real_name = data.get('real_name')
    age = data.get('age')
    occupation = data.get('occupation')
    learning_goal = data.get('learning_goal')
    role = data.get('role', 'user')
    
    if not username or not password:
        return jsonify({'error': '用户名和密码不能为空'}), 400
    
    # 检查用户名是否已存在
    existing_user = User.get_by_username(username)
    if existing_user:
        return jsonify({'error': '用户名已存在'}), 409
    
    user = User.create(
        username=username,
        password=password,
        nickname=nickname,
        real_name=real_name,
        age=age,
        occupation=occupation,
        learning_goal=learning_goal,
        role=role
    )
    
    return jsonify({
        'message': '用户创建成功',
        'user': user.to_dict()
    }), 201

@bp.route('/<int:user_id>', methods=['PUT'])
@login_required
def update_user(user_id):
    """更新用户信息"""
    if current_user.id != user_id and not current_user.is_admin():
        return jsonify({'error': '无权修改'}), 403
    
    user = User.get_by_id(user_id)
    if not user:
        return jsonify({'error': '用户不存在'}), 404
    
    data = request.get_json()
    
    # 普通用户不能修改角色
    if not current_user.is_admin() and 'role' in data:
        del data['role']
    
    user.update(**data)
    
    return jsonify({
        'message': '用户更新成功',
        'user': user.to_dict()
    })

@bp.route('/<int:user_id>', methods=['DELETE'])
@login_required
def delete_user(user_id):
    """删除用户（仅管理员）"""
    if not current_user.is_admin():
        return jsonify({'error': '无权操作'}), 403
    
    if user_id == current_user.id:
        return jsonify({'error': '不能删除自己'}), 400
    
    user = User.get_by_id(user_id)
    if not user:
        return jsonify({'error': '用户不存在'}), 404
    
    user.delete()
    return jsonify({'message': '用户删除成功'})

@bp.route('/<int:user_id>/profile', methods=['PUT'])
@login_required
def update_profile(user_id):
    """更新个人资料"""
    if current_user.id != user_id:
        return jsonify({'error': '无权修改'}), 403
    
    user = User.get_by_id(user_id)
    if not user:
        return jsonify({'error': '用户不存在'}), 404
    
    data = request.get_json()
    allowed_fields = ['nickname', 'real_name', 'age', 'occupation', 'learning_goal', 'avatar']
    update_data = {k: v for k, v in data.items() if k in allowed_fields}
    
    user.update(**update_data)
    
    return jsonify({
        'message': '资料更新成功',
        'user': user.to_dict()
    })
