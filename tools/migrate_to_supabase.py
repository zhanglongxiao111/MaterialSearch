#!/usr/bin/env python3
"""
数据迁移脚本: SQLite → Supabase (PostgreSQL)

将本地 SQLite 数据库中的图片和视频数据迁移到 Supabase。

使用方法:
    python tools/migrate_to_supabase.py --dry-run  # 预演模式
    python tools/migrate_to_supabase.py            # 实际迁移
"""
import argparse
import json
import logging
import os
import sys
from datetime import datetime
from typing import List, Dict, Any

import numpy as np

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

BATCH_SIZE = 100  # 每批处理的记录数


class MigrationStats:
    """迁移统计"""
    def __init__(self):
        self.images_total = 0
        self.images_migrated = 0
        self.images_failed = 0
        self.videos_total = 0
        self.videos_migrated = 0
        self.videos_failed = 0
        self.projects_total = 0
        self.projects_migrated = 0
        self.start_time = datetime.now()
    
    def summary(self) -> str:
        elapsed = (datetime.now() - self.start_time).total_seconds()
        return f"""
迁移统计:
  图片: {self.images_migrated}/{self.images_total} (失败: {self.images_failed})
  视频: {self.videos_migrated}/{self.videos_total} (失败: {self.videos_failed})
  项目: {self.projects_migrated}/{self.projects_total}
  耗时: {elapsed:.1f} 秒
"""


def get_sqlite_session(db_path: str):
    """获取 SQLite 数据库 session"""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    
    engine = create_engine(f'sqlite:///{db_path}')
    Session = sessionmaker(bind=engine)
    return Session()


def features_to_list(features_blob: bytes) -> List[float]:
    """将 SQLite 中的二进制特征转换为列表"""
    if not features_blob:
        return None
    
    arr = np.frombuffer(features_blob, dtype=np.float32)
    return arr.tolist()


def migrate_images(
    sqlite_session,
    supabase_client,
    stats: MigrationStats,
    dry_run: bool = False
) -> None:
    """迁移图片数据"""
    from models import Image
    
    logger.info("开始迁移图片...")
    
    # 统计总数
    stats.images_total = sqlite_session.query(Image).count()
    logger.info(f"共有 {stats.images_total} 张图片待迁移")
    
    if dry_run:
        logger.info("[DRY RUN] 跳过实际迁移")
        return
    
    # 分批处理
    offset = 0
    while offset < stats.images_total:
        images = sqlite_session.query(Image).offset(offset).limit(BATCH_SIZE).all()
        
        batch_data = []
        for img in images:
            record = {
                'path': img.path,
                'modify_time': img.modify_time.isoformat() if img.modify_time else None,
                'checksum': img.checksum,
                'width': img.width,
                'height': img.height,
                'aspect_ratio': img.aspect_ratio,
                'file_size': img.file_size,
                'file_format': img.file_format,
                'category': img.category,
                'design_style': img.design_style,
                'source_type': img.source_type or 'local',
                'is_deleted': img.is_deleted or False,
                'phash': img.phash,
                'features': features_to_list(img.features),
            }
            batch_data.append(record)
        
        try:
            # 插入到 Supabase
            response = supabase_client.table('images').insert(batch_data).execute()
            stats.images_migrated += len(batch_data)
            logger.info(f"已迁移 {stats.images_migrated}/{stats.images_total} 张图片")
        except Exception as e:
            stats.images_failed += len(batch_data)
            logger.error(f"批量插入失败: {e}")
        
        offset += BATCH_SIZE


def migrate_videos(
    sqlite_session,
    supabase_client,
    stats: MigrationStats,
    dry_run: bool = False
) -> None:
    """迁移视频数据"""
    from models import Video
    
    logger.info("开始迁移视频...")
    
    stats.videos_total = sqlite_session.query(Video).count()
    logger.info(f"共有 {stats.videos_total} 条视频帧待迁移")
    
    if dry_run:
        logger.info("[DRY RUN] 跳过实际迁移")
        return
    
    offset = 0
    while offset < stats.videos_total:
        videos = sqlite_session.query(Video).offset(offset).limit(BATCH_SIZE).all()
        
        batch_data = []
        for vid in videos:
            record = {
                'path': vid.path,
                'frame_time': vid.frame_time,
                'modify_time': vid.modify_time.isoformat() if vid.modify_time else None,
                'checksum': vid.checksum,
                'width': vid.width,
                'height': vid.height,
                'duration': vid.duration,
                'file_size': vid.file_size,
                'file_format': vid.file_format,
                'category': vid.category,
                'design_style': vid.design_style,
                'is_deleted': vid.is_deleted or False,
                'features': features_to_list(vid.features),
            }
            batch_data.append(record)
        
        try:
            response = supabase_client.table('videos').insert(batch_data).execute()
            stats.videos_migrated += len(batch_data)
            logger.info(f"已迁移 {stats.videos_migrated}/{stats.videos_total} 条视频帧")
        except Exception as e:
            stats.videos_failed += len(batch_data)
            logger.error(f"批量插入失败: {e}")
        
        offset += BATCH_SIZE


def migrate_projects(
    metadata_session,
    supabase_client,
    stats: MigrationStats,
    dry_run: bool = False
) -> None:
    """迁移项目数据"""
    from models import Project
    
    logger.info("开始迁移项目...")
    
    projects = metadata_session.query(Project).all()
    stats.projects_total = len(projects)
    logger.info(f"共有 {stats.projects_total} 个项目待迁移")
    
    if dry_run:
        logger.info("[DRY RUN] 跳过实际迁移")
        return
    
    for proj in projects:
        record = {
            'id': proj.id,
            'name': proj.name,
            'client_name': proj.client_name,
            'description': proj.description,
            'status': proj.status,
            'image_count': proj.image_count,
            'video_count': proj.video_count,
            'total_size': proj.total_size,
            'is_deleted': proj.is_deleted or False,
            'created_at': proj.created_time.isoformat() if proj.created_time else None,
        }
        
        try:
            supabase_client.table('projects').insert(record).execute()
            stats.projects_migrated += 1
        except Exception as e:
            logger.error(f"项目 {proj.id} 迁移失败: {e}")


def main():
    parser = argparse.ArgumentParser(description='迁移 SQLite 数据到 Supabase')
    parser.add_argument('--dry-run', action='store_true', help='预演模式，不实际写入')
    parser.add_argument('--permanent-db', default='./instance/permanent.db', help='永久库路径')
    parser.add_argument('--metadata-db', default='./instance/projects_metadata.db', help='元数据库路径')
    args = parser.parse_args()
    
    # 检查 Supabase 配置
    if not os.getenv('SUPABASE_URL') or not os.getenv('SUPABASE_ANON_KEY'):
        logger.error("请设置 SUPABASE_URL 和 SUPABASE_ANON_KEY 环境变量")
        sys.exit(1)
    
    # 连接数据库
    logger.info("连接数据库...")
    
    permanent_session = get_sqlite_session(args.permanent_db)
    metadata_session = get_sqlite_session(args.metadata_db)
    
    from app.integrations.supabase_client import get_supabase
    supabase_client = get_supabase()
    
    # 开始迁移
    stats = MigrationStats()
    
    if args.dry_run:
        logger.info("=== 预演模式 ===")
    
    migrate_projects(metadata_session, supabase_client, stats, args.dry_run)
    migrate_images(permanent_session, supabase_client, stats, args.dry_run)
    migrate_videos(permanent_session, supabase_client, stats, args.dry_run)
    
    # 输出统计
    print(stats.summary())
    
    permanent_session.close()
    metadata_session.close()
    
    logger.info("迁移完成!")


if __name__ == '__main__':
    main()
