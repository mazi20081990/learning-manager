import os
import json
import requests
import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

class LLMClient:
    """大模型API客户端，支持多Key轮换"""
    
    def __init__(self):
        """初始化LLM客户端"""
        self.api_keys = self._load_api_keys()
        self.api_base = os.getenv('LLM_API_BASE', 'https://api.siliconflow.cn/v1')
        # 使用更快的模型作为默认
        self.model = os.getenv('LLM_MODEL', 'Qwen/Qwen2.5-7B-Instruct')
        self.current_key_index = 0

    def _load_api_keys(self) -> List[str]:
        """加载API Keys（支持多Key轮询）"""
        keys_str = os.getenv('LLM_API_KEYS', '')
        if not keys_str:
            logger.warning('未配置LLM_API_KEYS')
            return []
        return [k.strip() for k in keys_str.split(',') if k.strip()]

    def _get_current_key(self) -> Optional[str]:
        """获取当前API Key"""
        if not self.api_keys:
            return None
        return self.api_keys[self.current_key_index]

    def _rotate_key(self):
        """轮换到下一个API Key"""
        if self.api_keys:
            self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
            logger.info(f'轮换到API Key {self.current_key_index + 1}/{len(self.api_keys)}')

    def chat(self, messages: List[Dict], temperature: float = 0.7,
             max_tokens: int = 2000, timeout: int = 120) -> Optional[str]:
        """
        调用LLM API

        Args:
            messages: 消息列表，格式为 [{"role": "user", "content": "..."}]
            temperature: 温度参数
            max_tokens: 最大token数
            timeout: 超时时间（秒）

        Returns:
            模型回复内容
        """
        if not self.api_keys:
            logger.error('未配置API Keys')
            return None

        # 尝试所有可用的Key
        for _ in range(len(self.api_keys)):
            api_key = self._get_current_key()
            if not api_key:
                break

            try:
                response = requests.post(
                    f'{self.api_base}/chat/completions',
                    headers={
                        'Authorization': f'Bearer {api_key}',
                        'Content-Type': 'application/json'
                    },
                    json={
                        'model': self.model,
                        'messages': messages,
                        'temperature': temperature,
                        'max_tokens': max_tokens
                    },
                    timeout=timeout
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if 'choices' in result and len(result['choices']) > 0:
                        content = result['choices'][0]['message']['content']
                        logger.info('LLM请求成功')
                        return content
                elif response.status_code == 401 or response.status_code == 403:
                    logger.warning(f'API Key无效，尝试下一个: {response.status_code}')
                    self._rotate_key()
                    continue
                else:
                    logger.error(f'LLM请求失败: {response.status_code} - {response.text}')
                    return None
                    
            except requests.exceptions.Timeout:
                logger.warning('LLM请求超时，尝试下一个Key')
                self._rotate_key()
                continue
            except Exception as e:
                logger.error(f'LLM请求异常: {e}')
                return None
        
        logger.error('所有API Keys均失败')
        return None
    
    def generate_plan(self, topic: str, days: int, mode: str = 'student') -> Optional[Dict]:
        """
        生成学习计划
        
        Args:
            topic: 学习主题
            days: 学习天数
            mode: 学习模式（student/work）
        
        Returns:
            学习计划字典
        """
        mode_desc = '学生模式（侧重理论理解和记忆）' if mode == 'student' else '工作模式（侧重实践应用和案例分析）'
        
        prompt = f"""请为"{topic}"生成一个{days}天的学习计划。

要求：
1. 学习模式：{mode_desc}
2. 由浅入深，循序渐进
3. **每一天必须有明确的、不同的子主题标题**，不能是"第X天"这种无意义的标题
4. 每一天的标题要具体说明当天学什么知识点
5. 输出JSON格式

**重要**：每一天的 title 必须是具体的知识点名称，例如：
- ❌ 错误："二年级数学提高 - 第1天"
- ✅ 正确："加法运算与进位规则"
- ✅ 正确："减法运算与退位规则"
- ✅ 正确："加减法混合运算"
- ✅ 正确："乘法口诀表（一）"
- ✅ 正确："乘法口诀表（二）"
- ✅ 正确："表内除法"
- ✅ 正确："混合运算顺序"
- ✅ 正确："应用题：购物问题"
- ✅ 正确："应用题：行程问题"

JSON格式：
{{
    "title": "计划标题",
    "description": "计划描述",
    "items": [
        {{
            "day_number": 1,
            "title": "第1天具体知识点名称",
            "description": "第1天学习内容的简要描述",
            "difficulty": "easy/medium/hard"
        }}
    ]
}}

请确保JSON格式正确，不要包含其他内容。"""

        messages = [{"role": "user", "content": prompt}]
        response = self.chat(messages, temperature=0.8, max_tokens=3000, timeout=30)
        
        if not response:
            return None
        
        try:
            # 提取JSON部分
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                json_str = response[json_start:json_end]
                plan = json.loads(json_str)
                return plan
            else:
                logger.error('无法从响应中提取JSON')
                return None
        except json.JSONDecodeError as e:
            logger.error(f'JSON解析失败: {e}')
            return None
    
    def generate_content(self, topic: str, title: str, search_results: List[Dict], mode: str = 'student') -> Optional[Dict]:
        """
        生成学习内容
        
        Args:
            topic: 学习主题
            title: 内容标题
            search_results: 搜索结果列表
            mode: 学习模式
        
        Returns:
            学习内容字典
        """
        # 构建搜索结果文本（精简）
        search_text = ""
        for i, result in enumerate(search_results[:3], 1):
            search_text += f"\n{i}. {result.get('title', '')}"
            if result.get('summary'):
                search_text += f" - {result.get('summary', '')[:100]}"

        mode_desc = '学生模式：侧重概念解释、理论推导和记忆要点' if mode == 'student' else '工作模式：侧重实际应用、案例分析和问题解决'

        prompt = f"""你是一位经验丰富的小学/初中数学老师，擅长从零开始教学。请为"{title}"生成一份适合零基础学生循序渐进学习的教学内容。

主题：{topic}
模式：{mode_desc}

参考资料：{search_text}

核心原则：**假设学生对这个知识点完全没有接触过，要从最基础的概念讲起，逐步递进。**

请严格按照以下四个部分生成Markdown内容，逻辑递进关系如下：

## 一、概念引入（占比15%）
- **用最简单的话**解释今天要学的核心概念是什么
- 给出**明确定义**，比如"什么是方程？必须同时含有未知数和等号的式子才是方程"
- 用正反例子对比说明：哪些是（如 3x+5=20），哪些不是（如 3+5=8，没有未知数；3x+5，没有等号）
- 用1-2个生活化类比帮助理解

## 二、方法讲解（占比25%）
- 详细讲解解决问题的**核心原理和操作步骤**
- 解释"为什么"要这样做，不是只告诉"怎么做"
  - 例如：为什么能移项？——等式两边同时加减同一个数，等式仍然成立
  - 为什么能合并同类项？——同类项表示相同类型的量，可以合并计算
  - 为什么要一边是未知数一边是数字？——这样才能求出未知数的值
- 用1-2个简单例子配合讲解，让学生理解原理
- 标注容易出错的地方

## 三、例题精讲（占比35%）
提供3-4道由易到难的**具体数学题**，每道题包含：
- **题目**：给出具体的数字和条件
- **解题过程**：详细展示每一步的计算和推导，在旁边注明每一步用了什么原理
- **答案**：明确的数字答案

题目类型要求：
- 第1题：最简单的直接计算题，巩固基本方法
- 第2题：稍复杂一点的计算或基础应用题
- 第3-4题：贴近生活的应用题，需要先找等量关系再列式计算

## 四、课堂练习（占比25%）
提供3-4道**具体练习题**，与例题知识点相同但数字不同：
- 难度循序渐进
- 每道题附带详细的解题过程和答案（用<details>标签折叠）
- 练习题要让学生独立完成，检测是否真正理解

输出JSON格式：
{{
    "title": "标题",
    "summary": "摘要（150字以内，概括本节核心内容）",
    "content": "上述四个部分的完整Markdown内容",
    "key_points": ["要点1", "要点2", "要点3", "要点4", "要点5"],
    "references": []
}}

只输出JSON，不要输出其他任何内容。"""

        messages = [{"role": "user", "content": prompt}]
        response = self.chat(messages, temperature=0.7, max_tokens=4000, timeout=45)
        
        if not response:
            return None
        
        try:
            # 尝试多种方式提取JSON
            json_str = None

            # 方式1：查找 ```json 代码块
            if '```json' in response:
                start = response.find('```json') + 7
                end = response.find('```', start)
                if end > start:
                    json_str = response[start:end].strip()
            # 方式2：查找 ``` 代码块
            elif '```' in response:
                start = response.find('```') + 3
                end = response.find('```', start)
                if end > start:
                    json_str = response[start:end].strip()

            # 方式3：直接查找JSON对象
            if not json_str:
                json_start = response.find('{')
                json_end = response.rfind('}') + 1
                if json_start >= 0 and json_end > json_start:
                    json_str = response[json_start:json_end]

            if json_str:
                content = json.loads(json_str)
                logger.info('JSON解析成功')
                return content
            else:
                logger.error(f'无法从响应中提取JSON，响应内容：{response[:200]}')
                return None
        except json.JSONDecodeError as e:
            logger.error(f'JSON解析失败: {e}，响应内容：{response[:200]}')
            return None
    
    def generate_exam_questions(self, topic: str, content: str, num_questions: int = 5) -> Optional[List[Dict]]:
        """
        生成考试题目
        
        Args:
            topic: 学习主题
            content: 学习内容
            num_questions: 题目数量
        
        Returns:
            题目列表
        """
        prompt = f"""请根据以下学习内容生成{num_questions}道考试题目。

学习主题：{topic}

学习内容：
{content[:2000]}...

要求：
1. 题目类型必须包含以下五种：单选题、多选题、判断题、填空题、简答题
2. 每种类型至少1道题，其余可自由分配
3. 每道题包含题目、选项（选择题/判断题需要）、正确答案、详细解析
4. 难度分布：简单、中等、困难各占约三分之一
5. 填空题的答案要明确，简答题要给出要点式的参考答案
6. 输出JSON格式

JSON格式：
{{
    "questions": [
        {{
            "type": "single_choice",
            "question": "题目内容",
            "options": ["选项A", "选项B", "选项C", "选项D"],
            "correct_answer": "正确答案",
            "explanation": "详细答案解析",
            "difficulty": "easy"
        }},
        {{
            "type": "fill_blank",
            "question": "___是计算机科学的核心概念之一。",
            "options": [],
            "correct_answer": "算法",
            "explanation": "详细答案解析",
            "difficulty": "easy"
        }},
        {{
            "type": "short_answer",
            "question": "请简述XXX的主要特点。",
            "options": [],
            "correct_answer": "1. 特点一；2. 特点二；3. 特点三",
            "explanation": "详细答案解析",
            "difficulty": "medium"
        }}
    ]
}}

type可选值：single_choice（单选题）、multiple_choice（多选题）、true_false（判断题）、fill_blank（填空题）、short_answer（简答题）

请确保JSON格式正确，不要包含其他内容。"""

        messages = [{"role": "user", "content": prompt}]
        response = self.chat(messages, temperature=0.8, max_tokens=3000)
        
        if not response:
            return None
        
        try:
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                json_str = response[json_start:json_end]
                data = json.loads(json_str)
                return data.get('questions', [])
            else:
                logger.error('无法从响应中提取JSON')
                return None
        except json.JSONDecodeError as e:
            logger.error(f'JSON解析失败: {e}')
            return None
    
    def generate_image_prompt(self, content_summary: str) -> Optional[str]:
        """
        生成图片提示词
        
        Args:
            content_summary: 内容摘要
        
        Returns:
            图片提示词
        """
        prompt = f"""请为以下内容生成一个图片提示词，用于AI生成手绘风格的教学插图。

内容摘要：{content_summary}

要求：
1. 提示词为英文
2. 描述清晰，包含场景、元素、风格
3. 适合教学场景
4. 手绘风格，简洁明了
5. 仅输出提示词，不要其他内容

示例：
"Hand-drawn educational illustration of [topic], simple and clear, white background, sketch style, suitable for learning materials"

请生成提示词："""

        messages = [{"role": "user", "content": prompt}]
        response = self.chat(messages, temperature=0.7, max_tokens=500)
        
        if response:
            # 清理提示词
            prompt_text = response.strip().strip('"').strip("'")
            return prompt_text
        return None
    
    def answer_question(self, question: str, context: str = '') -> Optional[str]:
        """
        回答用户问题
        
        Args:
            question: 用户问题
            context: 上下文内容
        
        Returns:
            回答内容
        """
        prompt = f"""请回答以下学习相关问题。

上下文内容：
{context[:1000]}...

用户问题：{question}

要求：
1. 回答准确、清晰
2. 如果涉及概念，请简要解释
3. 如果涉及应用，请提供示例
4. 保持简洁，不要过度展开"""

        messages = [{"role": "user", "content": prompt}]
        return self.chat(messages, temperature=0.7, max_tokens=1500)
