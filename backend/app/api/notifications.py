from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from app.utils.notification import NotificationManager
from app.utils.mita_search import MitaSearch

bp = Blueprint('notifications', __name__, url_prefix='/api/notifications')
notifier = NotificationManager()

@bp.route('/test', methods=['POST'])
@login_required
def test_notification():
    """测试推送通知"""
    data = request.get_json()
    channel = data.get('channel', 'dingtalk')
    message = data.get('message', '这是一条测试消息')
    title = data.get('title', '推送测试')
    
    if channel == 'dingtalk':
        result = notifier.send_dingtalk(message, title)
    elif channel == 'wechat':
        result = notifier.send_wechat(message, title)
    elif channel == 'serverchan':
        result = notifier.send_serverchan(message, title)
    else:
        return jsonify({'error': '未知的推送渠道'}), 400
    
    if result:
        return jsonify({'message': '测试消息发送成功'})
    else:
        return jsonify({'error': '测试消息发送失败'}), 500

@bp.route('/test-all', methods=['POST'])
@login_required
def test_all_notifications():
    """测试所有推送渠道"""
    results = notifier.test_all_channels()
    return jsonify({
        'message': '测试完成',
        'results': results
    })

@bp.route('/quota', methods=['GET'])
@login_required
def get_search_quota():
    """获取搜索额度状态"""
    mita = MitaSearch()
    quota = mita.get_quota_status()
    return jsonify({'quota': quota})
