import os
from flask import Blueprint, request, jsonify, send_file
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app.models.plan import LearningPlan
from app.utils.image_generator import ImageGenerator

bp = Blueprint('images', __name__, url_prefix='/api/images')
image_gen = ImageGenerator()

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@bp.route('/upload', methods=['POST'])
@login_required
def upload_image():
    """上传图片"""
    if 'file' not in request.files:
        return jsonify({'error': '没有文件'}), 400
    
    file = request.files['file']
    plan_id = request.form.get('plan_id')
    
    if file.filename == '':
        return jsonify({'error': '未选择文件'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'error': '不支持的文件格式'}), 400
    
    # 检查权限
    if plan_id:
        plan = LearningPlan.get_by_id(int(plan_id))
        if plan and plan.user_id != current_user.id and not current_user.is_admin():
            return jsonify({'error': '无权上传'}), 403
    
    # 保存文件
    filename = secure_filename(file.filename)
    if plan_id:
        upload_dir = os.path.join(image_gen.nas_base_path, str(plan_id))
    else:
        upload_dir = image_gen.nas_base_path
    
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, filename)
    file.save(file_path)
    
    return jsonify({
        'message': '图片上传成功',
        'filename': filename,
        'path': file_path
    })

@bp.route('/<path:filename>', methods=['GET'])
@login_required
def get_image(filename):
    """获取图片"""
    # 从请求参数中获取计划ID
    plan_id = request.args.get('plan_id')
    
    if plan_id:
        image_path = os.path.join(image_gen.nas_base_path, str(plan_id), filename)
    else:
        image_path = os.path.join(image_gen.nas_base_path, filename)
    
    if not os.path.exists(image_path):
        # 返回占位图
        placeholder = image_gen.get_placeholder_image()
        if placeholder:
            return send_file(placeholder)
        return jsonify({'error': '图片不存在'}), 404
    
    return send_file(image_path)

@bp.route('/delete', methods=['POST'])
@login_required
def delete_image():
    """删除图片"""
    data = request.get_json()
    image_path = data.get('path')
    
    if not image_path:
        return jsonify({'error': '图片路径不能为空'}), 400
    
    # 检查权限
    # 简化处理，实际应该检查图片所属计划的用户权限
    
    result = image_gen.delete_image(image_path)
    if result:
        return jsonify({'message': '图片删除成功'})
    else:
        return jsonify({'error': '图片删除失败'}), 500

@bp.route('/info', methods=['GET'])
@login_required
def get_image_info():
    """获取图片信息"""
    image_path = request.args.get('path')
    
    if not image_path:
        return jsonify({'error': '图片路径不能为空'}), 400
    
    info = image_gen.get_image_info(image_path)
    if info:
        return jsonify({'info': info})
    else:
        return jsonify({'error': '获取图片信息失败'}), 500
