"""
素材服务

封装素材处理业务逻辑。
"""
import os
import logging
from typing import Optional, Tuple
from io import BytesIO

from PIL import Image as PILImage

logger = logging.getLogger(__name__)

TEMP_PATH = os.getenv('TEMP_PATH', './tmp')


class AssetService:
    """
    素材服务类
    
    提供素材的上传、获取和处理功能。
    """
    
    def __init__(self, target: str = 'permanent'):
        self.target = target
    
    def upload_file(self, file_stream, original_filename: str = "") -> str:
        """
        上传文件到临时目录
        
        Args:
            file_stream: 文件流
            original_filename: 原始文件名
        
        Returns:
            临时文件路径
        """
        from utils import get_hash
        
        filehash = get_hash(file_stream)
        upload_dir = f"{TEMP_PATH}/upload"
        os.makedirs(upload_dir, exist_ok=True)
        
        upload_path = f"{upload_dir}/{filehash}"
        
        # 保存文件
        file_stream.seek(0)
        with open(upload_path, 'wb') as f:
            f.write(file_stream.read())
        
        return upload_path
    
    def get_image(self, image_id: int, thumbnail: bool = False) -> Optional[Tuple[bytes, str]]:
        """
        获取图片
        
        Args:
            image_id: 图片 ID
            thumbnail: 是否返回缩略图
        
        Returns:
            (图片数据, MIME类型) 或 None
        """
        from app.repositories.image_repo import get_image_repository
        from utils import resize_image_with_aspect_ratio
        
        repo = get_image_repository(self.target)
        image = repo.find_by_id(image_id)
        
        if not image:
            return None
        
        if thumbnail:
            img = resize_image_with_aspect_ratio(image.path, (640, 480), convert_rgb=True)
            img_io = BytesIO()
            img.save(img_io, 'JPEG', quality=60)
            return img_io.getvalue(), 'image/jpeg'
        
        # 检查文件是否存在
        if not os.path.exists(image.path):
            return None
        
        # 读取原始文件
        with open(image.path, 'rb') as f:
            data = f.read()
        
        # 根据扩展名确定 MIME 类型
        ext = os.path.splitext(image.path)[1].lower()
        mime_types = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.webp': 'image/webp',
            '.bmp': 'image/bmp',
        }
        mime = mime_types.get(ext, 'application/octet-stream')
        
        return data, mime
    
    def get_video_clip(
        self, 
        video_path: str, 
        start_time: int, 
        end_time: int
    ) -> Optional[str]:
        """
        获取视频片段
        
        Args:
            video_path: 视频路径
            start_time: 开始时间（秒）
            end_time: 结束时间（秒）
        
        Returns:
            视频片段路径或 None
        """
        from utils import crop_video
        
        if not os.path.exists(video_path):
            return None
        
        output_dir = f"{TEMP_PATH}/video_clips"
        os.makedirs(output_dir, exist_ok=True)
        
        output_path = f"{output_dir}/{start_time}_{end_time}_{os.path.basename(video_path)}"
        
        if not os.path.exists(output_path):
            crop_video(video_path, output_path, start_time, end_time)
        
        return output_path


# 服务实例缓存
_asset_service_cache = {}


def get_asset_service(target: str = 'permanent') -> AssetService:
    """获取素材服务实例"""
    if target not in _asset_service_cache:
        _asset_service_cache[target] = AssetService(target)
    return _asset_service_cache[target]
