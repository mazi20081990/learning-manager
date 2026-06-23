import os
import io
import json
import requests
import logging
from PIL import Image
from typing import Optional, List, Dict
from datetime import datetime

logger = logging.getLogger(__name__)

class ImageGenerator:
    """图片生成器，使用Pollinations.ai免费API"""
    
    def __init__(self):
        self.api_base = 'https://image.pollinations.ai/prompt'
        self.nas_base_path = os.getenv('NAS_IMAGE_PATH', '/data/images')
        self.nas_base_url = os.getenv('NAS_BASE_URL', '')
        self.placeholder_image = 'static/images/placeholder.png'
    
    def _ensure_dir(self, path: str):
        """确保目录存在"""
        os.makedirs(path, exist_ok=True)
    
    def _generate_filename(self, plan_id: int, topic: str, index: int) -> str:
        """生成文件名"""
        # 清理主题名称，移除特殊字符
        clean_topic = ''.join(c for c in topic if c.isalnum() or c in (' ', '-', '_')).strip()
        clean_topic = clean_topic.replace(' ', '_')[:50]
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        return f"{plan_id}_{clean_topic}_{index}_{timestamp}"
    
    def generate_image(self, prompt: str, width: int = 1024, height: int = 768, 
                      seed: Optional[int] = None) -> Optional[bytes]:
        """
        生成图片
        
        Args:
            prompt: 图片提示词
            width: 图片宽度
            height: 图片高度
            seed: 随机种子
        
        Returns:
            图片二进制数据
        """
        try:
            # 构建URL参数
            params = {
                'width': width,
                'height': height,
                'nologo': 'true',
                'enhance': 'true'
            }
            if seed:
                params['seed'] = seed
            
            # URL编码提示词
            encoded_prompt = requests.utils.quote(prompt)
            url = f"{self.api_base}/{encoded_prompt}"
            
            logger.info(f'生成图片: {prompt[:100]}...')
            
            response = requests.get(
                url,
                params=params,
                timeout=120,
                stream=True
            )
            
            if response.status_code == 200:
                image_data = response.content
                logger.info(f'图片生成成功: {len(image_data)} bytes')
                return image_data
            else:
                logger.error(f'图片生成失败: {response.status_code}')
                return None
                
        except requests.exceptions.Timeout:
            logger.warning('图片生成超时')
            return None
        except Exception as e:
            logger.error(f'图片生成异常: {e}')
            return None
    
    def process_image(self, image_data: bytes, filename: str, 
                     output_dir: str) -> Optional[Dict]:
        """
        处理图片（压缩、转换格式、生成多尺寸）
        
        Args:
            image_data: 图片二进制数据
            filename: 文件名（不含扩展名）
            output_dir: 输出目录
        
        Returns:
            图片信息字典
        """
        try:
            self._ensure_dir(output_dir)
            
            # 打开图片
            img = Image.open(io.BytesIO(image_data))
            original_width, original_height = img.size
            
            # 转换为RGB（处理RGBA等模式）
            if img.mode in ('RGBA', 'P'):
                img = img.convert('RGB')
            
            # 生成原图（WebP格式）
            original_path = os.path.join(output_dir, f'{filename}.webp')
            img.save(original_path, 'WEBP', quality=85)
            
            # 生成预览图（宽度800px）
            preview_img = img.copy()
            preview_width = 800
            preview_height = int(preview_width * original_height / original_width)
            preview_img = preview_img.resize((preview_width, preview_height), Image.Resampling.LANCZOS)
            preview_path = os.path.join(output_dir, f'{filename}_preview.webp')
            preview_img.save(preview_path, 'WEBP', quality=80)
            
            # 生成缩略图（宽度300px）
            thumb_img = img.copy()
            thumb_width = 300
            thumb_height = int(thumb_width * original_height / original_width)
            thumb_img = thumb_img.resize((thumb_width, thumb_height), Image.Resampling.LANCZOS)
            thumb_path = os.path.join(output_dir, f'{filename}_thumb.webp')
            thumb_img.save(thumb_path, 'WEBP', quality=75)
            
            # 获取文件大小
            original_size = os.path.getsize(original_path)
            
            return {
                'filename': f'{filename}.webp',
                'original_path': original_path,
                'preview_path': preview_path,
                'thumbnail_path': thumb_path,
                'width': original_width,
                'height': original_height,
                'file_size': original_size,
                'format': 'WEBP'
            }
            
        except Exception as e:
            logger.error(f'图片处理失败: {e}')
            return None
    
    def generate_for_content(self, plan_id: int, item_id: int, topic: str, 
                            content_summary: str, num_images: int = 2) -> List[Dict]:
        """
        为学习内容生成图片
        
        Args:
            plan_id: 计划ID
            item_id: 项目ID
            topic: 学习主题
            content_summary: 内容摘要
            num_images: 图片数量
        
        Returns:
            图片信息列表
        """
        from app.utils.llm_client import LLMClient
        
        llm = LLMClient()
        output_dir = os.path.join(self.nas_base_path, str(plan_id))
        self._ensure_dir(output_dir)
        
        images_info = []
        
        for i in range(num_images):
            # 生成提示词
            prompt = llm.generate_image_prompt(content_summary)
            if not prompt:
                logger.warning('生成图片提示词失败，使用默认提示词')
                prompt = f"Hand-drawn educational illustration of {topic}, simple and clear, white background, sketch style"
            
            # 添加手绘风格前缀
            full_prompt = f"Hand-drawn sketch style, educational illustration, {prompt}, simple and clear, white background, suitable for learning materials"
            
            # 生成图片
            image_data = self.generate_image(full_prompt, width=1024, height=768)
            if not image_data:
                logger.warning(f'第{i+1}张图片生成失败')
                continue
            
            # 处理图片
            filename = self._generate_filename(plan_id, topic, i+1)
            image_info = self.process_image(image_data, filename, output_dir)
            
            if image_info:
                # 构建访问URL
                if self.nas_base_url:
                    image_info['url'] = f"{self.nas_base_url}/images/{plan_id}/{image_info['filename']}"
                    image_info['preview_url'] = f"{self.nas_base_url}/images/{plan_id}/{filename}_preview.webp"
                    image_info['thumbnail_url'] = f"{self.nas_base_url}/images/{plan_id}/{filename}_thumb.webp"
                
                image_info['plan_id'] = plan_id
                image_info['item_id'] = item_id
                image_info['is_auto_generated'] = True
                image_info['description'] = prompt
                
                images_info.append(image_info)
                logger.info(f'第{i+1}张图片生成成功')
            else:
                logger.warning(f'第{i+1}张图片处理失败')
        
        return images_info
    
    def get_placeholder_image(self) -> str:
        """获取占位图路径"""
        if os.path.exists(self.placeholder_image):
            return self.placeholder_image
        
        # 创建默认占位图
        try:
            self._ensure_dir('static/images')
            img = Image.new('RGB', (800, 600), color='#f0f0f0')
            img.save(self.placeholder_image, 'PNG')
            return self.placeholder_image
        except Exception as e:
            logger.error(f'创建占位图失败: {e}')
            return ''
    
    def delete_image(self, image_path: str) -> bool:
        """
        删除图片
        
        Args:
            image_path: 图片路径
        
        Returns:
            是否删除成功
        """
        try:
            if os.path.exists(image_path):
                os.remove(image_path)
                logger.info(f'图片已删除: {image_path}')
                return True
            return False
        except Exception as e:
            logger.error(f'删除图片失败: {e}')
            return False
    
    def get_image_info(self, image_path: str) -> Optional[Dict]:
        """
        获取图片信息
        
        Args:
            image_path: 图片路径
        
        Returns:
            图片信息字典
        """
        try:
            if not os.path.exists(image_path):
                return None
            
            img = Image.open(image_path)
            file_size = os.path.getsize(image_path)
            
            return {
                'path': image_path,
                'width': img.width,
                'height': img.height,
                'format': img.format,
                'file_size': file_size,
                'mode': img.mode
            }
        except Exception as e:
            logger.error(f'获取图片信息失败: {e}')
            return None
