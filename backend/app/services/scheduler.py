import os
import logging
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from app.models.plan import LearningPlan, PlanItem
from app.services.content_service import ContentService
from app.models.database import get_db

logger = logging.getLogger(__name__)

# 全局调度器
scheduler = None

def start_scheduler():
    """启动定时任务调度器"""
    global scheduler
    
    if scheduler is not None and scheduler.running:
        logger.info('调度器已在运行')
        return
    
    scheduler = BackgroundScheduler()
    
    # 每日学习内容生成任务（早上8点）
    scheduler.add_job(
        generate_daily_content,
        trigger=CronTrigger(hour=8, minute=0),
        id='daily_content_generation',
        name='每日学习内容生成',
        replace_existing=True
    )
    
    # 每日学习提醒任务（早上8点30分）
    scheduler.add_job(
        send_daily_reminders,
        trigger=CronTrigger(hour=8, minute=30),
        id='daily_reminders',
        name='每日学习提醒',
        replace_existing=True
    )
    
    # 每周备份任务（每周日凌晨2点）
    scheduler.add_job(
        weekly_backup,
        trigger=CronTrigger(day_of_week='sun', hour=2, minute=0),
        id='weekly_backup',
        name='每周数据备份',
        replace_existing=True
    )
    
    scheduler.start()
    logger.info('定时任务调度器已启动')

def stop_scheduler():
    """停止定时任务调度器"""
    global scheduler
    
    if scheduler is not None and scheduler.running:
        scheduler.shutdown()
        logger.info('定时任务调度器已停止')

def generate_daily_content():
    """生成每日学习内容"""
    try:
        logger.info('开始生成每日学习内容')
        
        # 获取所有进行中的计划
        db = get_db()
        rows = db.execute(
            "SELECT id FROM learning_plans WHERE status = 'active'"
        ).fetchall()
        
        content_service = ContentService()
        
        for row in rows:
            plan_id = row['id']
            plan = LearningPlan.get_by_id(plan_id)
            
            if not plan:
                continue
            
            # 获取当前进行中的项目
            current_item = plan.get_current_item()
            if not current_item:
                continue
            
            # 检查是否已生成内容
            existing_content = current_item.get_content()
            if existing_content:
                logger.info(f'计划{plan_id}的项目{current_item.id}已有内容，跳过')
                continue
            
            # 生成内容
            content = content_service.generate_content(plan_id, current_item.id)
            if content:
                logger.info(f'计划{plan_id}的项目{current_item.id}内容生成成功')
            else:
                logger.warning(f'计划{plan_id}的项目{current_item.id}内容生成失败')
        
        logger.info('每日学习内容生成完成')
        
    except Exception as e:
        logger.error(f'生成每日内容失败: {e}')

def send_daily_reminders():
    """发送每日学习提醒"""
    try:
        logger.info('开始发送每日学习提醒')
        
        # 获取所有进行中的计划
        db = get_db()
        rows = db.execute(
            "SELECT id FROM learning_plans WHERE status = 'active'"
        ).fetchall()
        
        content_service = ContentService()
        
        for row in rows:
            plan_id = row['id']
            plan = LearningPlan.get_by_id(plan_id)
            
            if not plan:
                continue
            
            # 获取当前进行中的项目
            current_item = plan.get_current_item()
            if not current_item:
                continue
            
            # 发送通知
            result = content_service.send_daily_notification(plan_id, current_item.id)
            if result:
                logger.info(f'计划{plan_id}的提醒发送成功')
            else:
                logger.warning(f'计划{plan_id}的提醒发送失败')
        
        logger.info('每日学习提醒发送完成')
        
    except Exception as e:
        logger.error(f'发送每日提醒失败: {e}')

def weekly_backup():
    """每周数据备份"""
    try:
        logger.info('开始每周数据备份')
        
        # 备份SQLite数据库
        import shutil
        from datetime import datetime
        
        db_path = 'data/learning_manager.db'
        backup_dir = 'data/backups'
        os.makedirs(backup_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = os.path.join(backup_dir, f'learning_manager_{timestamp}.db')
        
        if os.path.exists(db_path):
            shutil.copy2(db_path, backup_path)
            logger.info(f'数据库备份完成: {backup_path}')
        
        # 清理旧备份（保留最近4周）
        cleanup_old_backups(backup_dir, keep_count=4)
        
        logger.info('每周数据备份完成')
        
    except Exception as e:
        logger.error(f'每周备份失败: {e}')

def cleanup_old_backups(backup_dir: str, keep_count: int = 4):
    """清理旧备份文件"""
    try:
        backups = sorted(
            [f for f in os.listdir(backup_dir) if f.startswith('learning_manager_')],
            reverse=True
        )
        
        for old_backup in backups[keep_count:]:
            old_path = os.path.join(backup_dir, old_backup)
            os.remove(old_path)
            logger.info(f'删除旧备份: {old_path}')
            
    except Exception as e:
        logger.error(f'清理旧备份失败: {e}')


