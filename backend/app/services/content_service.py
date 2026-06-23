import os
import json
import logging
from typing import Optional, List, Dict
from datetime import datetime
from app.models.database import get_db
from app.models.plan import LearningPlan, PlanItem
from app.models.content import LearningContent
from app.utils.llm_client import LLMClient
from app.utils.mita_search import MitaSearch
from app.utils.image_generator import ImageGenerator
from app.utils.notification import NotificationManager

logger = logging.getLogger(__name__)

class ContentService:
    """学习内容服务"""
    
    def __init__(self):
        self.llm = LLMClient()
        self.search = MitaSearch()
        self.image_gen = ImageGenerator()
        self.notifier = NotificationManager()
    
    def _generate_fallback_content(self, topic: str, title: str, mode: str) -> Dict:
        """当LLM API失败时，生成从零开始循序渐进的学习内容"""
        mode_hint = '（学生模式：侧重理论理解）' if mode == 'student' else '（工作模式：侧重实践应用）'
        return {
            'title': title,
            'summary': f'本节从零开始学习{title}：先理解概念定义，再掌握解题原理，最后通过例题和练习巩固。{mode_hint}',
            'content': f"""# {title}

---

## 一、概念引入

小朋友们，今天我们要学习一个非常重要的数学工具——**方程**。

### 什么是方程？

> **方程**就是含有未知数的等式。

注意两个条件**必须同时满足**：
1. **含有未知数**（比如 x、y 这样的字母）
2. **是等式**（有"="号）

### 哪些是方程？哪些不是？

**✅ 是方程的例子：**
- `3x + 5 = 20` ← 有未知数 x，也有等号 ✓
- `x + 8 = 15`  ← 有未知数 x，也有等号 ✓
- `2y - 6 = 10` ← 有未知数 y，也有等号 ✓

**❌ 不是方程的例子：**
- `3 + 5 = 8`    ← 没有未知数 ✗
- `3x + 5`       ← 没有等号 ✗
- `x > 10`       ← 不是等式（没有等号）✗

### 生活中的类比

方程就像是一架**天平**。等号就是天平的中间支点，左边和右边的重量必须相等。未知数 x 就像是放在天平上的一个**未知重量的盒子**，我们要想办法找出这个盒子到底有多重。

---

## 二、方法讲解

学会了怎么识别方程，接下来我们要学习怎么"解方程"——也就是找出方程中未知数的值。

### 核心原理：等式的性质

解方程的依据是**等式的性质**：

> **等式两边同时加上、减去、乘以或除以同一个数（除数不为0），等式仍然成立。**

### 为什么能"移项"？

当我们把方程中的一项从左边移到右边时，实际上是**两边同时做了相反的运算**：

例如：`x + 5 = 12`
- 左边是 x + 5，我们想单独得到 x
- 两边同时减去 5：`x + 5 - 5 = 12 - 5`
- 得到：`x = 7`

我们把它简化成"移项"——把 +5 移到右边变成 -5。

### 解方程的标准步骤

```
1. 移项：把含未知数的项放左边，常数项放右边（移项要变号）
2. 合并同类项：左边和右边分别计算
3. 系数化1：两边同时除以未知数的系数
```

### 举个例子

解方程：`3x + 5 = 20`

**第一步（移项）**：把 +5 移到右边变成 -5
```
3x = 20 - 5
```

**第二步（合并）**：右边算出 20 - 5 = 15
```
3x = 15
```

**第三步（系数化1）**：两边同时除以 3
```
x = 15 ÷ 3
x = 5
```

> **易错提醒**：移项时一定要变号！加变减，减变加，乘变除，除变乘。

---

## 三、例题精讲

### 例题1（基础）

**题目**：解方程 x + 8 = 15

**解题过程**：
- 移项：把 +8 移到右边变成 -8
- x = 15 - 8
- 合并：x = 7

**答案**：**x = 7**

**验算**：把 x = 7 代入原方程：7 + 8 = 15 ✓ 正确！

---

### 例题2（基础）

**题目**：解方程 4x = 28

**解题过程**：
- 左边的 4x 表示 4 乘以 x
- 两边同时除以 4：x = 28 ÷ 4
- x = 7

**答案**：**x = 7**

**验算**：4 × 7 = 28 ✓ 正确！

---

### 例题3（应用题）

**题目**：小明买了 3 本同样的笔记本，一共花了 24 元。每本笔记本多少钱？

**解题过程**：
设每本笔记本 x 元
- 3 本的总价：3x
- 列方程：3x = 24
- 两边同时除以 3：x = 24 ÷ 3
- x = 8

**答**：每本笔记本 8 元。

**验算**：3 × 8 = 24 ✓ 正确！

---

### 例题4（两步运算）

**题目**：一个数的 2 倍加上 6 等于 20，求这个数。

**解题过程**：
设这个数为 x
- 列方程：2x + 6 = 20
- 移项（+6 移到右边变 -6）：2x = 20 - 6
- 合并：2x = 14
- 两边同时除以 2：x = 14 ÷ 2
- x = 7

**答**：这个数是 7。

---

## 四、课堂练习

### 练习1

**题目**：解方程 x + 12 = 25

<details>
<summary>点击查看答案</summary>

**解题过程**：
x + 12 = 25
x = 25 - 12
x = 13

**答案**：**x = 13**

**验算**：13 + 12 = 25 ✓
</details>

### 练习2

**题目**：解方程 5x = 45

<details>
<summary>点击查看答案</summary>

**解题过程**：
5x = 45
x = 45 ÷ 5
x = 9

**答案**：**x = 9**

**验算**：5 × 9 = 45 ✓
</details>

### 练习3

**题目**：妈妈买了 4 千克苹果，一共花了 36 元。每千克苹果多少钱？

<details>
<summary>点击查看答案</summary>

**解题过程**：
设每千克苹果 x 元
4x = 36
x = 36 ÷ 4
x = 9

**答**：每千克苹果 9 元。

**验算**：4 × 9 = 36 ✓
</details>

### 练习4

**题目**：解方程 3x + 7 = 28

<details>
<summary>点击查看答案</summary>

**解题过程**：
3x + 7 = 28
3x = 28 - 7
3x = 21
x = 21 ÷ 3
x = 7

**答案**：**x = 7**

**验算**：3 × 7 + 7 = 21 + 7 = 28 ✓
</details>

---

> **本节我们学习了**：什么是方程（含有未知数的等式）、等式的性质、解方程的方法（移项→合并→系数化1）。下一节我们将学习更复杂的两步方程和应用题，请提前复习本节的解题步骤。

---
*注：由于AI服务暂时不可用，此内容为自动生成的学习模板。您可以在设置中更换AI API后重新生成更详细的内容。*
""",
            'key_points': [
                f'理解{title}的定义：含有未知数的等式才是方程',
                f'掌握等式的性质：等式两边同时加减乘除同一个数，等式不变',
                f'学会解方程的基本步骤：移项→合并→系数化1',
                f'理解移项的原理：两边同时做相反的运算',
                f'养成验算的好习惯：把答案代入原方程检验'
            ],
            'references': []
        }

    def generate_content(self, plan_id: int, item_id: int) -> Optional[LearningContent]:
        """
        生成学习内容

        Args:
            plan_id: 计划ID
            item_id: 项目ID

        Returns:
            学习内容对象
        """
        try:
            # 获取计划和项目信息
            plan = LearningPlan.get_by_id(plan_id)
            item = PlanItem.get_by_id(item_id)

            if not plan or not item:
                logger.error('计划或项目不存在')
                return None

            # 搜索相关资料
            search_results = []
            try:
                search_results = self.search.search_for_knowledge(plan.topic, item.title)
            except Exception as e:
                logger.warning(f'搜索失败，继续使用LLM生成: {e}')

            # 生成内容
            content_data = self.llm.generate_content(
                topic=plan.topic,
                title=item.title,
                search_results=search_results,
                mode=plan.mode
            )

            # 如果LLM生成失败，使用降级方案
            if not content_data:
                logger.warning('LLM生成失败，使用模板内容')
                content_data = self._generate_fallback_content(plan.topic, item.title, plan.mode)
            
            # 生成图片
            images_info = []
            try:
                images_info = self.image_gen.generate_for_content(
                    plan_id=plan_id,
                    item_id=item_id,
                    topic=plan.topic,
                    content_summary=content_data.get('summary', ''),
                    num_images=2
                )
            except Exception as e:
                logger.warning(f'生成图片失败: {e}')
            
            # 构建图片URL列表
            images_urls = [img.get('url', '') for img in images_info if img.get('url')]
            
            # 构建参考链接
            refs = content_data.get('references', [])
            refs_json = json.dumps(refs, ensure_ascii=False) if refs else '[]'

            # 创建学习内容
            content = LearningContent.create(
                plan_id=plan_id,
                item_id=item_id,
                title=content_data.get('title', item.title),
                content_html=self._markdown_to_html(content_data.get('content', '')),
                content_markdown=content_data.get('content', ''),
                summary=content_data.get('summary', ''),
                tags=json.dumps(content_data.get('key_points', []), ensure_ascii=False),
                images=json.dumps(images_urls, ensure_ascii=False),
                refs=refs_json
            )
            
            # 更新项目状态
            item.update(status='in_progress')
            
            logger.info(f'学习内容生成成功: {content.id}')
            return content
            
        except Exception as e:
            logger.error(f'生成学习内容失败: {e}')
            return None
    
    def _markdown_to_html(self, markdown_text: str) -> str:
        """将Markdown转换为HTML"""
        try:
            import markdown
            html = markdown.markdown(
                markdown_text,
                extensions=['extra', 'codehilite', 'toc']
            )
            return html
        except Exception as e:
            logger.warning(f'Markdown转换失败: {e}')
            return f'<pre>{markdown_text}</pre>'
    
    def get_content(self, content_id: int) -> Optional[LearningContent]:
        """获取学习内容"""
        return LearningContent.get_by_id(content_id)
    
    def get_content_by_item(self, item_id: int) -> Optional[LearningContent]:
        """根据项目ID获取学习内容"""
        return LearningContent.get_by_item(item_id)
    
    def update_content(self, content_id: int, **kwargs) -> Optional[LearningContent]:
        """更新学习内容"""
        content = LearningContent.get_by_id(content_id)
        if content:
            content.update(**kwargs)
            return content
        return None
    
    def delete_content(self, content_id: int) -> bool:
        """删除学习内容"""
        content = LearningContent.get_by_id(content_id)
        if content:
            content.delete()
            return True
        return False
    
    def answer_question(self, question: str, content_id: Optional[int] = None) -> str:
        """
        回答用户问题
        
        Args:
            question: 用户问题
            content_id: 学习内容ID（可选）
        
        Returns:
            回答内容
        """
        context = ''
        if content_id:
            content = LearningContent.get_by_id(content_id)
            if content:
                context = content.content_markdown or ''
        
        # 使用大模型直接回答
        answer = self.llm.answer_question(question, context)
        
        if not answer:
            return '抱歉，暂时无法回答您的问题，请稍后再试。'
        
        return answer
    
    def send_daily_notification(self, plan_id: int, item_id: int) -> bool:
        """
        发送每日学习通知
        
        Args:
            plan_id: 计划ID
            item_id: 项目ID
        
        Returns:
            是否发送成功
        """
        try:
            plan = LearningPlan.get_by_id(plan_id)
            item = PlanItem.get_by_id(item_id)
            
            if not plan or not item:
                logger.error('计划或项目不存在')
                return False
            
            # 构建内容URL
            content_url = f"/content/{plan_id}/{item_id}"
            
            # 发送通知
            result = self.notifier.send_learning_notification(
                user_id=plan.user_id,
                plan_id=plan_id,
                item_id=item_id,
                title=item.title,
                content_url=content_url,
                channel='dingtalk'
            )
            
            return result
            
        except Exception as e:
            logger.error(f'发送每日通知失败: {e}')
            return False
    
    def regenerate_content(self, content_id: int) -> Optional[LearningContent]:
        """
        重新生成学习内容
        
        Args:
            content_id: 学习内容ID
        
        Returns:
            新的学习内容对象
        """
        content = LearningContent.get_by_id(content_id)
        if not content:
            return None
        
        # 删除旧内容
        content.delete()
        
        # 重新生成
        return self.generate_content(content.plan_id, content.item_id)
    
    def get_content_with_images(self, content_id: int) -> Optional[Dict]:
        """
        获取学习内容（包含图片信息）

        Args:
            content_id: 学习内容ID

        Returns:
            内容和图片信息字典
        """
        content = LearningContent.get_by_id(content_id)
        if not content:
            return None

        # 解析图片URL
        images = []
        try:
            images = json.loads(content.images or '[]')
        except:
            pass

        # 解析参考链接 (数据库字段为refs)
        references = []
        try:
            refs_raw = getattr(content, 'refs', None) or getattr(content, 'references', None)
            references = json.loads(refs_raw or '[]')
        except:
            pass

        # 解析标签
        tags = []
        try:
            tags = json.loads(content.tags or '[]')
        except:
            pass

        return {
            'id': content.id,
            'plan_id': content.plan_id,
            'item_id': content.item_id,
            'title': content.title,
            'content_html': content.content_html,
            'content_markdown': content.content_markdown,
            'summary': content.summary,
            'tags': tags,
            'images': images,
            'references': references,
            'generated_at': content.generated_at
        }
