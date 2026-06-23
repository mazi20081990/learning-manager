import json
import logging
from typing import Optional, List, Dict
from app.models.database import get_db
from app.models.plan import LearningPlan, PlanItem
from app.utils.llm_client import LLMClient

logger = logging.getLogger(__name__)

class PlanService:
    """学习计划服务"""
    
    def __init__(self):
        self.llm = LLMClient()
    
    def create_plan(self, user_id: int, topic: str, days: int,
                   mode: str = 'student', description: Optional[str] = None,
                   learner_id: Optional[int] = None) -> Optional[LearningPlan]:
        """
        创建学习计划

        Args:
            user_id: 用户ID
            topic: 学习主题
            days: 学习天数
            mode: 学习模式
            description: 计划描述
            learner_id: 学习者ID（可选）

        Returns:
            学习计划对象
        """
        try:
            # 使用大模型生成计划
            plan_data = self.llm.generate_plan(topic, days, mode)
            logger.info(f'LLM generate_plan returned: {type(plan_data)} = {str(plan_data)[:200]}')
            
            # 如果LLM生成失败，使用降级方案
            if not plan_data:
                logger.warning('LLM生成计划失败，使用模板计划')
                plan_data = self._generate_fallback_plan(topic, days, mode)

            # 创建计划
            plan = LearningPlan.create(
                user_id=user_id,
                learner_id=learner_id,
                title=plan_data.get('title', f'{topic}学习计划'),
                topic=topic,
                total_days=days,
                mode=mode,
                description=description or plan_data.get('description', '')
            )

            # 创建计划项目
            items = plan_data.get('items', [])
            for item_data in items:
                PlanItem.create(
                    plan_id=plan.id,
                    day_number=item_data.get('day_number', 1),
                    title=item_data.get('title', ''),
                    description=item_data.get('description', ''),
                    difficulty=item_data.get('difficulty', 'medium')
                )

            logger.info(f'学习计划创建成功: {plan.id}')
            return plan

        except Exception as e:
            logger.error(f'Create plan failed: {e}', exc_info=True)
            return None
    
    def _generate_fallback_plan(self, topic: str, days: int, mode: str) -> Dict:
        """当LLM API失败时，生成带有具体子主题的模板计划"""
        # 根据主题和天数生成具体的子主题
        subtopics = self._generate_subtopics(topic, days)
        items = []
        for i in range(1, days + 1):
            subtopic = subtopics[i - 1] if i <= len(subtopics) else f'{topic}进阶内容（第{i}天）'
            items.append({
                'day_number': i,
                'title': subtopic,
                'description': f'学习{subtopic}的相关知识和应用',
                'difficulty': 'easy' if i <= days // 3 else ('medium' if i <= 2 * days // 3 else 'hard')
            })
        return {
            'title': f'{topic}{days}天学习计划',
            'description': f'系统学习{topic}，共{days}天，由浅入深',
            'items': items
        }

    def _generate_subtopics(self, topic: str, days: int) -> List[str]:
        """根据主题和天数生成具体的子主题列表"""
        topic_lower = topic.lower()

        # 数学相关主题
        math_keywords = ['数学', '方程', '代数', '几何', '算术', '计算', '加减', '乘除', '分数', '小数', '百分数', '比例', '面积', '周长', '体积']
        if any(kw in topic_lower for kw in math_keywords):
            return self._math_subtopics(topic, days)

        # 英语相关主题
        english_keywords = ['英语', '英文', '语法', '单词', '词汇', '阅读', '写作', '听力', '口语']
        if any(kw in topic_lower for kw in english_keywords):
            return self._english_subtopics(topic, days)

        # 语文相关主题
        chinese_keywords = ['语文', '汉字', '拼音', '阅读', '作文', '写作', '古诗词', '文言文']
        if any(kw in topic_lower for kw in chinese_keywords):
            return self._chinese_subtopics(topic, days)

        # 科学/物理/化学
        science_keywords = ['物理', '化学', '科学', '生物', '自然']
        if any(kw in topic_lower for kw in science_keywords):
            return self._science_subtopics(topic, days)

        # 编程相关
        code_keywords = ['编程', 'python', '代码', '程序', '算法', '计算机']
        if any(kw in topic_lower for kw in code_keywords):
            return self._coding_subtopics(topic, days)

        # 默认通用主题
        return self._default_subtopics(topic, days)

    def _math_subtopics(self, topic: str, days: int) -> List[str]:
        """数学主题子主题"""
        # 根据主题判断具体方向
        if '方程' in topic:
            templates = [
                '认识方程：什么是方程',
                '等式的性质',
                '解简单方程（一步运算）',
                '解两步方程',
                '解方程应用题（和差问题）',
                '解方程应用题（倍数问题）',
                '解方程应用题（行程问题）',
                '解方程应用题（工程问题）',
                '复杂方程与综合练习',
                '方程单元复习与测试'
            ]
        elif '加减' in topic or '加法' in topic or '减法' in topic:
            templates = [
                '加法运算与进位规则',
                '减法运算与退位规则',
                '加减法混合运算',
                '加减法应用题（购物问题）',
                '加减法应用题（比较问题）',
                '加减法速算技巧',
                '加减法估算',
                '加减法综合练习',
                '加减法易错题分析',
                '加减法单元复习'
            ]
        elif '乘' in topic or '除' in topic:
            templates = [
                '乘法口诀表（一）：1-5',
                '乘法口诀表（二）：6-9',
                '表内乘法应用',
                '表内除法',
                '乘除法混合运算',
                '有余数的除法',
                '乘除法应用题',
                '倍数与因数',
                '乘除法综合练习',
                '乘除法单元复习'
            ]
        elif '分数' in topic:
            templates = [
                '认识分数',
                '分数的大小比较',
                '同分母分数加减法',
                '异分母分数加减法',
                '分数乘法',
                '分数除法',
                '分数与小数的互化',
                '分数应用题',
                '分数混合运算',
                '分数单元复习'
            ]
        elif '几何' in topic or '图形' in topic:
            templates = [
                '认识基本图形',
                '线段、射线与直线',
                '角的度量',
                '三角形（一）：分类与性质',
                '三角形（二）：内角和',
                '四边形',
                '长方形与正方形',
                '平行四边形与梯形',
                '周长与面积计算',
                '几何综合复习'
            ]
        else:
            templates = [
                '数的认识与读写',
                '数的比较与排序',
                '基本运算规则',
                '混合运算顺序',
                '应用题：和差问题',
                '应用题：倍数问题',
                '应用题：行程问题',
                '应用题：工程问题',
                '综合计算练习',
                '单元复习与测试'
            ]
        return templates[:days] + [f'{topic}综合内容（第{i}天）' for i in range(len(templates) + 1, days + 1)]

    def _english_subtopics(self, topic: str, days: int) -> List[str]:
        """英语主题子主题"""
        templates = [
            '基础词汇（一）：日常用语',
            '基础词汇（二）：家庭成员',
            '基础词汇（三）：学校生活',
            '一般现在时',
            '一般过去时',
            '一般将来时',
            '现在进行时',
            '形容词与副词',
            '阅读理解技巧',
            '写作基础与练习'
        ]
        return templates[:days] + [f'{topic}进阶内容（第{i}天）' for i in range(len(templates) + 1, days + 1)]

    def _chinese_subtopics(self, topic: str, days: int) -> List[str]:
        """语文主题子主题"""
        templates = [
            '汉字基础：笔画与笔顺',
            '汉字基础：偏旁部首',
            '拼音规则（一）：声母',
            '拼音规则（二）：韵母',
            '词语搭配与运用',
            '句子成分分析',
            '阅读理解方法',
            '作文：写人',
            '作文：记事',
            '古诗词赏析'
        ]
        return templates[:days] + [f'{topic}进阶内容（第{i}天）' for i in range(len(templates) + 1, days + 1)]

    def _science_subtopics(self, topic: str, days: int) -> List[str]:
        """科学主题子主题"""
        templates = [
            '科学观察方法',
            '物质的性质',
            '力与运动',
            '简单机械',
            '光与声',
            '电与磁',
            '植物的生长',
            '动物的特征',
            '地球与宇宙',
            '科学实验与探究'
        ]
        return templates[:days] + [f'{topic}进阶内容（第{i}天）' for i in range(len(templates) + 1, days + 1)]

    def _coding_subtopics(self, topic: str, days: int) -> List[str]:
        """编程主题子主题"""
        templates = [
            '编程基础：变量与数据类型',
            '编程基础：输入与输出',
            '条件语句：if-else',
            '循环语句：for循环',
            '循环语句：while循环',
            '函数的定义与调用',
            '列表与字典',
            '字符串处理',
            '文件读写',
            '综合项目实践'
        ]
        return templates[:days] + [f'{topic}进阶内容（第{i}天）' for i in range(len(templates) + 1, days + 1)]

    def _default_subtopics(self, topic: str, days: int) -> List[str]:
        """通用主题子主题"""
        templates = [
            f'{topic}基础概念',
            f'{topic}核心原理',
            f'{topic}基本方法',
            f'{topic}简单应用',
            f'{topic}进阶技巧（一）',
            f'{topic}进阶技巧（二）',
            f'{topic}综合应用',
            f'{topic}常见错误分析',
            f'{topic}提高训练',
            f'{topic}总结与复习'
        ]
        return templates[:days]

    def get_plan(self, plan_id: int) -> Optional[LearningPlan]:
        """获取学习计划"""
        return LearningPlan.get_by_id(plan_id)
    
    def get_user_plans(self, user_id: int, status: Optional[str] = None, learner_id: Optional[int] = None) -> List[LearningPlan]:
        """获取用户的学习计划"""
        if learner_id:
            return LearningPlan.get_by_learner(learner_id, status)
        return LearningPlan.get_by_user(user_id, status)
    
    def update_plan(self, plan_id: int, **kwargs) -> Optional[LearningPlan]:
        """更新学习计划"""
        plan = LearningPlan.get_by_id(plan_id)
        if plan:
            plan.update(**kwargs)
            return plan
        return None
    
    def delete_plan(self, plan_id: int) -> bool:
        """删除学习计划"""
        plan = LearningPlan.get_by_id(plan_id)
        if plan:
            plan.delete()
            return True
        return False
    
    def add_plan_item(self, plan_id: int, day_number: int, title: str, 
                     description: Optional[str] = None, difficulty: str = 'medium') -> Optional[PlanItem]:
        """添加计划项目"""
        return PlanItem.create(plan_id, day_number, title, description, difficulty)
    
    def update_plan_item(self, item_id: int, **kwargs) -> Optional[PlanItem]:
        """更新计划项目"""
        item = PlanItem.get_by_id(item_id)
        if item:
            item.update(**kwargs)
            return item
        return None
    
    def delete_plan_item(self, item_id: int) -> bool:
        """删除计划项目"""
        item = PlanItem.get_by_id(item_id)
        if item:
            item.delete()
            return True
        return False
    
    def complete_item(self, item_id: int, mastery_level: Optional[int] = None) -> Optional[PlanItem]:
        """完成计划项目"""
        item = PlanItem.get_by_id(item_id)
        if item:
            item.complete(mastery_level)
            return item
        return None
    
    def get_plan_progress(self, plan_id: int) -> Dict:
        """获取计划进度"""
        plan = LearningPlan.get_by_id(plan_id)
        if not plan:
            return {}
        
        items = plan.get_items()
        total = len(items)
        completed = sum(1 for item in items if item.status == 'completed')
        in_progress = sum(1 for item in items if item.status == 'in_progress')
        pending = sum(1 for item in items if item.status == 'pending')
        
        return {
            'plan_id': plan_id,
            'total': total,
            'completed': completed,
            'in_progress': in_progress,
            'pending': pending,
            'progress_percentage': round((completed / total * 100), 2) if total > 0 else 0
        }
    
    def recommend_days(self, topic: str) -> int:
        """根据主题自动推荐学习天数"""
        if not topic:
            return 7

        length = len(topic)

        # 常见的完整科目 → 30天
        complete_subjects = [
            '小学数学', '初中数学', '高中数学', '小学语文', '初中语文', '高中语文',
            '小学英语', '初中英语', '高中英语', 'Python基础', 'Python入门',
            'Java基础', 'C语言基础', '前端开发', '后端开发', '数据结构',
            '数据库基础', 'Linux基础', '机器学习', '深度学习'
        ]
        for subject in complete_subjects:
            if subject in topic:
                return 30

        # 综合/复杂主题（7字以上）→ 15-21天
        if length >= 7:
            return 21

        # 较复杂知识点（5-6字）→ 10-14天
        if length >= 5:
            return 14

        # 中等知识点（3-4字）→ 5-7天
        if length >= 3:
            return 7

        # 简单知识点（2字以内）→ 3天
        return 3

    def batch_generate_content(self, plan_id: int) -> None:
        """在后台为计划的所有项目预生成内容"""
        try:
            plan = LearningPlan.get_by_id(plan_id)
            if not plan:
                return
            items = plan.get_items()
            from app.services.content_service import ContentService
            content_service = ContentService()
            for item in items:
                try:
                    # 检查是否已有内容
                    from app.models.content import LearningContent
                    existing = LearningContent.get_by_item(item.id)
                    if not existing:
                        content_service.generate_content(plan_id, item.id)
                except Exception as e:
                    logger.error(f'预生成内容失败 item={item.id}: {e}')
        except Exception as e:
            logger.error(f'批量生成内容失败: {e}')

    def get_templates(self) -> List[Dict]:
        """获取预设模板"""
        return [
            {
                'id': 'quick_start',
                'name': '快速入门',
                'days': 7,
                'description': '7天快速掌握基础知识，每天1-2小时',
                'icon': '⚡'
            },
            {
                'id': 'systematic',
                'name': '系统学习',
                'days': 30,
                'description': '30天系统学习，每天1小时',
                'icon': '📚'
            },
            {
                'id': 'deep_learning',
                'name': '深度学习',
                'days': 90,
                'description': '90天深度学习，每天30分钟',
                'icon': '🎯'
            }
        ]
    
    def pause_plan(self, plan_id: int) -> Optional[LearningPlan]:
        """暂停学习计划"""
        return self.update_plan(plan_id, status='paused')
    
    def resume_plan(self, plan_id: int) -> Optional[LearningPlan]:
        """恢复学习计划"""
        return self.update_plan(plan_id, status='active')
    
    def archive_plan(self, plan_id: int) -> Optional[LearningPlan]:
        """归档学习计划"""
        return self.update_plan(plan_id, status='archived')
