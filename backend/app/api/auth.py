from flask import Blueprint, request, jsonify, session
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash
from app.models.user import User

bp = Blueprint('auth', __name__, url_prefix='/api/auth')

@bp.route('/login', methods=['POST'])
def login():
    """用户登录"""
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'error': '用户名和密码不能为空'}), 400
    
    user = User.get_by_username(username)
    if not user:
        return jsonify({'error': '用户不存在'}), 404
    
    if not check_password_hash(user.password_hash, password):
        return jsonify({'error': '密码错误'}), 401
    
    if not user.is_active:
        return jsonify({'error': '用户已被禁用'}), 403
    
    login_user(user, remember=True)
    session.permanent = True
    
    return jsonify({
        'message': '登录成功',
        'user': user.to_dict()
    })

@bp.route('/logout', methods=['POST'])
@login_required
def logout():
    """用户登出"""
    logout_user()
    return jsonify({'message': '登出成功'})

@bp.route('/me', methods=['GET'])
@login_required
def get_current_user():
    """获取当前用户信息"""
    return jsonify({
        'user': current_user.to_dict()
    })

@bp.route('/change-password', methods=['POST'])
@login_required
def change_password():
    """修改密码"""
    data = request.get_json()
    old_password = data.get('old_password')
    new_password = data.get('new_password')
    
    if not old_password or not new_password:
        return jsonify({'error': '旧密码和新密码不能为空'}), 400
    
    if not check_password_hash(current_user.password_hash, old_password):
        return jsonify({'error': '旧密码错误'}), 401
    
    current_user.set_password(new_password)
    current_user.update(password_hash=current_user.password_hash)
    
    return jsonify({'message': '密码修改成功'})
