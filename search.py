import base64
import logging
import os
import time
from functools import lru_cache

import numpy as np

from config import *
from database import (
    get_image_id_path_features_filter_by_path_time,
    get_image_features_by_id,
    get_video_paths,
    get_frame_times_features_by_path,
    get_pexels_video_features,
    get_session_by_target,
    get_db_manager,
    get_pdf_page_features,
)
from models import DatabaseSession, DatabaseSessionPexelsVideo
from process_assets import match_batch, process_image, process_text

logger = logging.getLogger(__name__)


def clean_cache():
    """
    清空搜索缓存
    """
    search_image_by_text_path_time.cache_clear()
    search_image_by_image.cache_clear()
    search_video_by_image.cache_clear()
    search_video_by_text_path_time.cache_clear()
    search_pexels_video_by_text.cache_clear()


def _get_source_label(library_type, project_id=None):
    """
    获取搜索结果来源标签
    :param library_type: string, 库类型 'permanent' / 'project'
    :param project_id: string, 项目ID
    :return: string, 来源标签
    """
    if library_type == "permanent":
        return "永久库"
    elif library_type == "project" and project_id:
        try:
            from project_manager import get_project_manager
            pm = get_project_manager()
            project = pm.get_project(project_id)
            if project:
                return f"项目: {project['name']}"
            return f"项目: {project_id}"
        except Exception:
            return f"项目: {project_id}"
    return "未知"


def search_image_by_feature(
        positive_feature=None,
        negative_feature=None,
        positive_threshold=POSITIVE_THRESHOLD,
        negative_threshold=NEGATIVE_THRESHOLD,
        filter_path="",
        start_time=None,
        end_time=None,
        session=None,
        exclude_duplicates=False,
):
    """
    通过特征搜索图片
    :param positive_feature: np.array, 正向特征向量
    :param negative_feature: np.array, 反向特征向量
    :param positive_threshold: int/float, 正向阈值
    :param negative_threshold: int/float, 反向阈值
    :param filter_path: string, 图片路径
    :param start_time: int, 时间范围筛选开始时间戳，单位秒，用于匹配modify_time
    :param end_time: int, 时间范围筛选结束时间戳，单位秒，用于匹配modify_time
    :param session: Session, 可选的数据库会话对象，用于指定搜索的数据库
    :return: list[dict], 搜索结果列表
    """
    t0 = time.time()

    # 如果提供了 session，使用它；否则创建新的 DatabaseSession
    if session is not None:
        ids, paths, features = get_image_id_path_features_filter_by_path_time(
            session, filter_path, start_time, end_time, exclude_duplicates=exclude_duplicates)
        pdf_entries = get_pdf_page_features(session, filter_path, start_time, end_time, only_primary=True)
    else:
        with DatabaseSession() as default_session:
            ids, paths, features = get_image_id_path_features_filter_by_path_time(
                default_session, filter_path, start_time, end_time, exclude_duplicates=exclude_duplicates)
            pdf_entries = get_pdf_page_features(default_session, filter_path, start_time, end_time, only_primary=True)

    combined_bytes = []
    meta = []

    for id, path, feature_bytes in zip(ids, paths, features):
        if not feature_bytes:
            continue
        combined_bytes.append(feature_bytes)
        meta.append({
            "type": "image",
            "id": int(id) if id is not None else None,
            "path": path
        })

    for entry in pdf_entries or []:
        feat = entry.get("features")
        if not feat:
            continue
        combined_bytes.append(feat)
        meta.append({
            "type": "pdf",
            "id": entry.get("id"),
            "path": entry.get("source_path"),
            "page_no": entry.get("page_no"),
            "page_count": entry.get("page_count"),
            "pages_truncated": entry.get("pages_truncated"),
            "thumbnail_path": entry.get("thumbnail_path"),
            "width": entry.get("width"),
            "height": entry.get("height"),
            "file_size": entry.get("file_size"),
        })

    if len(combined_bytes) == 0:  # 没有素材，直接返回空
        return []
    features_np = np.frombuffer(b"".join(combined_bytes), dtype=np.float32).reshape(len(combined_bytes), -1)
    scores = match_batch(positive_feature, negative_feature, features_np, positive_threshold, negative_threshold)
    return_list = []

    # 确定目标库用于URL生成
    if session is not None:
        # 尝试确定 session 的目标
        if hasattr(session.bind, 'url'):
            url_str = str(session.bind.url)
            if 'permanent.db' in url_str:
                url_target = 'permanent'
            elif 'proj_' in url_str:
                # 提取项目ID
                import re
                match = re.search(r'proj_[^_]+_[^_]+_\d+\.db', url_str)
                url_target = match.group(0).replace('.db', '') if match else 'permanent'
            else:
                url_target = 'permanent'
        else:
            url_target = 'permanent'
    else:
        url_target = 'permanent'

    for item, score in zip(meta, scores):
        if not score:
            continue
        if item.get("type") == "pdf":
            page_id = item.get("id")
            return_list.append({
                "id": page_id,
                "url": f"api/pdf/page/{page_id}?target={url_target}",
                "thumbnail": f"api/pdf/page/{page_id}?target={url_target}&size=512",
                "path": item.get("path"),
                "doc_path": item.get("path"),
                "page_no": item.get("page_no"),
                "page_count": item.get("page_count"),
                "pages_truncated": item.get("pages_truncated"),
                "type": "pdf",
                "filename": os.path.basename(item.get("path") or "") if item.get("path") else "",
                "width": item.get("width"),
                "height": item.get("height"),
                "size": item.get("file_size"),
                "score": float(score),
            })
        else:
            img_id = item.get("id")
            path = item.get("path")
            return_list.append({
                "id": img_id,
                "url": f"api/get_image/{img_id}?target={url_target}",
                "path": path,
                "type": "image",
                "score": float(score),
            })
    return_list = sorted(return_list, key=lambda x: x["score"], reverse=True)
    logger.info("查询使用时间：%.2f" % (time.time() - t0))
    return return_list


@lru_cache(maxsize=CACHE_SIZE)
def search_image_by_text_path_time(
        positive_prompt="",
        negative_prompt="",
        positive_threshold=POSITIVE_THRESHOLD,
        negative_threshold=NEGATIVE_THRESHOLD,
        filter_path="",
        start_time=None,
        end_time=None,
        library_type="permanent",
        project_id=None,
        include_duplicates=False,
):
    """
    使用文字搜图片
    :param positive_prompt: string, 正向提示词
    :param negative_prompt: string, 反向提示词
    :param positive_threshold: int/float, 正向阈值
    :param negative_threshold: int/float, 反向阈值
    :param filter_path: string, 图片路径
    :param start_time: int, 时间范围筛选开始时间戳，单位秒，用于匹配modify_time
    :param end_time: int, 时间范围筛选结束时间戳，单位秒，用于匹配modify_time
    :param library_type: string, 库类型 'permanent' / 'project'
    :param project_id: string, 项目ID (library_type='project' 时必填)
    :return: list[dict], 搜索结果列表
    """
    positive_feature = process_text(positive_prompt)
    negative_feature = process_text(negative_prompt)

    # 根据库类型获取session
    if library_type == "permanent":
        target = "permanent"
    elif library_type == "project":
        if not project_id:
            raise ValueError("library_type='project' 时必须提供 project_id")
        target = project_id
    else:
        raise ValueError(f"不支持的 library_type: {library_type}")

    try:
        session = get_session_by_target(target)
    except (ValueError, FileNotFoundError):
        # 如果获取失败，回退到默认session
        session = DatabaseSession()

    # 执行搜索
    with session:
        results = search_image_by_feature(
            positive_feature, negative_feature,
            positive_threshold, negative_threshold,
            filter_path, start_time, end_time,
            session=session,
            exclude_duplicates=(library_type == "permanent" and not include_duplicates)
        )

    # 添加来源标注
    source_label = _get_source_label(library_type, project_id)
    for result in results:
        result['source'] = source_label

    return results


@lru_cache(maxsize=CACHE_SIZE)
def search_image_by_image(
        img_id_or_path,
        threshold=IMAGE_THRESHOLD,
        filter_path="",
        start_time=None,
        end_time=None,
        library_type="permanent",
        project_id=None,
        include_duplicates=False,
):
    """
    使用图片搜图片
    :param img_id_or_path: int/string, 图片ID 或 图片路径
    :param threshold: int/float, 搜索阈值
    :param filter_path: string, 图片路径
    :param start_time: int, 时间范围筛选开始时间戳，单位秒，用于匹配modify_time
    :param end_time: int, 时间范围筛选结束时间戳，单位秒，用于匹配modify_time
    :param library_type: string, 库类型 'permanent' / 'project'
    :param project_id: string, 项目ID (library_type='project' 时必填)
    :return: list[dict], 搜索结果列表
    """
    # 根据库类型获取session
    if library_type == "permanent":
        target = "permanent"
    elif library_type == "project":
        if not project_id:
            raise ValueError("library_type='project' 时必须提供 project_id")
        target = project_id
    else:
        raise ValueError(f"不支持的 library_type: {library_type}")

    try:
        session = get_session_by_target(target)
    except (ValueError, FileNotFoundError):
        session = DatabaseSession()

    try:  # 前端点击以图搜图，通过图片id来搜图 注意：如果后面id改成str的话，需要修改这部分
        img_id = int(img_id_or_path)
        with session:
            features = get_image_features_by_id(session, img_id)
        if not features:
            return []
        features = np.frombuffer(features, dtype=np.float32).reshape(1, -1)
    except ValueError:  # 传入路径，通过上传的图片来搜图
        img_path = img_id_or_path
        features = process_image(img_path)

    # 执行搜索
    with session:
        results = search_image_by_feature(
            features, None, threshold, None, filter_path, start_time, end_time,
            session=session,
            exclude_duplicates=(library_type == "permanent" and not include_duplicates)
        )

    # 添加来源标注
    source_label = _get_source_label(library_type, project_id)
    for result in results:
        result['source'] = source_label

    return results


def get_index_pairs(scores):
    """
    根据每一帧的余弦相似度计算素材片段
    :param scores: [<class 'numpy.nparray'>], 余弦相似度列表，里面每个元素的shape=(1, 1)
    :return: 返回连续的帧序号列表，如第2-5帧、第11-13帧都符合搜索内容，则返回[(2,5),(11,13)]
    """
    indexes = []
    for i in range(len(scores)):
        if scores[i]:
            indexes.append(i)
    result = []
    start_index = -1
    for i in range(len(indexes)):
        if start_index == -1:
            start_index = indexes[i]
        elif indexes[i] - indexes[i - 1] > 2:  # 允许中间空1帧
            result.append((start_index, indexes[i - 1]))
            start_index = indexes[i]
    if start_index != -1:
        result.append((start_index, indexes[-1]))
    return result


def get_video_range(start_index, end_index, scores, frame_times):
    """
    根据帧数范围，获取视频时长范围
    """
    # 间隔小于等于2倍FRAME_INTERVAL的算为同一个素材，同时开始时间和结束时间各延长0.5个FRAME_INTERVAL
    if start_index > 0:
        start_time = int((frame_times[start_index] + frame_times[start_index - 1]) / 2)
    else:
        start_time = frame_times[start_index]
    if end_index < len(scores) - 1:
        end_time = int((frame_times[end_index] + frame_times[end_index + 1]) / 2 + 0.5)
    else:
        end_time = frame_times[end_index]
    return start_time, end_time


def search_video_by_feature(
        positive_feature=None,
        negative_feature=None,
        positive_threshold=POSITIVE_THRESHOLD,
        negative_threshold=NEGATIVE_THRESHOLD,
        filter_path="",
        modify_time_start=None,
        modify_time_end=None,
        session=None,
):
    """
    通过特征搜索视频
    :param positive_feature: np.array, 正向特征向量
    :param negative_feature: np.array, 反向特征向量
    :param positive_threshold: int/float, 正向阈值
    :param negative_threshold: int/float, 反向阈值
    :param filter_path: string, 视频路径
    :param modify_time_start: int, 时间范围筛选开始时间戳，单位秒，用于匹配modify_time
    :param modify_time_end: int, 时间范围筛选结束时间戳，单位秒，用于匹配modify_time
    :param session: Session, 可选的数据库会话对象，用于指定搜索的数据库
    :return: list[dict], 搜索结果列表
    """
    t0 = time.time()

    # 如果提供了 session，使用它；否则创建新的 DatabaseSession
    if session is not None:
        video_paths = get_video_paths(session, filter_path, modify_time_start, modify_time_end)
    else:
        with DatabaseSession() as default_session:
            video_paths = get_video_paths(default_session, filter_path, modify_time_start, modify_time_end)

    return_list = []
    session_use = session if session is not None else DatabaseSession()

    for path in video_paths:  # 逐个视频比对
        if session is not None:
            frame_times, features = get_frame_times_features_by_path(session, path)
        else:
            with session_use as s:
                frame_times, features = get_frame_times_features_by_path(s, path)

        features = np.frombuffer(b"".join(features), dtype=np.float32).reshape(len(features), -1)
        scores = match_batch(positive_feature, negative_feature, features, positive_threshold, negative_threshold)
        index_pairs = get_index_pairs(scores)
        for start_index, end_index in index_pairs:
            score = max(scores[start_index: end_index + 1])
            start_time, end_time = get_video_range(start_index, end_index, scores, frame_times)
            return_list.append({
                "url": "api/get_video/%s" % base64.urlsafe_b64encode(path.encode()).decode()
                       + "#t=%.1f,%.1f" % (start_time, end_time),
                "path": path,
                "score": float(score),
                "start_time": start_time,
                "end_time": end_time,
            })

    logger.info("查询使用时间：%.2f" % (time.time() - t0))
    return_list = sorted(return_list, key=lambda x: x["score"], reverse=True)
    return return_list


@lru_cache(maxsize=CACHE_SIZE)
def search_video_by_text_path_time(
        positive_prompt="",
        negative_prompt="",
        positive_threshold=POSITIVE_THRESHOLD,
        negative_threshold=NEGATIVE_THRESHOLD,
        filter_path="",
        start_time=None,
        end_time=None,
        library_type="permanent",
        project_id=None,
):
    """
    使用文字搜视频
    :param positive_prompt: string, 正向提示词
    :param negative_prompt: string, 反向提示词
    :param positive_threshold: int/float, 正向阈值
    :param negative_threshold: int/float, 反向阈值
    :param filter_path: string, 视频路径
    :param start_time: int, 时间范围筛选开始时间戳，单位秒，用于匹配modify_time
    :param end_time: int, 时间范围筛选结束时间戳，单位秒，用于匹配modify_time
    :param library_type: string, 库类型 'permanent' / 'project'
    :param project_id: string, 项目ID (library_type='project' 时必填)
    :return: list[dict], 搜索结果列表
    """
    positive_feature = process_text(positive_prompt)
    negative_feature = process_text(negative_prompt)

    # 根据库类型获取session
    if library_type == "permanent":
        target = "permanent"
    elif library_type == "project":
        if not project_id:
            raise ValueError("library_type='project' 时必须提供 project_id")
        target = project_id
    else:
        raise ValueError(f"不支持的 library_type: {library_type}")

    try:
        session = get_session_by_target(target)
    except (ValueError, FileNotFoundError):
        session = DatabaseSession()

    with session:
        results = search_video_by_feature(positive_feature, negative_feature, positive_threshold, negative_threshold, filter_path, start_time, end_time, session=session)

    # 添加来源标注
    source_label = _get_source_label(library_type, project_id)
    for result in results:
        result['source'] = source_label

    return results


@lru_cache(maxsize=CACHE_SIZE)
def search_video_by_image(
        img_id_or_path,
        threshold=IMAGE_THRESHOLD,
        filter_path="",
        start_time=None,
        end_time=None,
        library_type="permanent",
        project_id=None,
):
    """
    使用图片搜视频
    :param img_id_or_path: int/string, 图片ID 或 图片路径
    :param threshold: int/float, 搜索阈值
    :param filter_path: string, 视频路径
    :param start_time: int, 时间范围筛选开始时间戳，单位秒，用于匹配modify_time
    :param end_time: int, 时间范围筛选结束时间戳，单位秒，用于匹配modify_time
    :param library_type: string, 库类型 'permanent' / 'project'
    :param project_id: string, 项目ID (library_type='project' 时必填)
    :return: list[dict], 搜索结果列表
    """
    # 根据库类型获取session
    if library_type == "permanent":
        target = "permanent"
    elif library_type == "project":
        if not project_id:
            raise ValueError("library_type='project' 时必须提供 project_id")
        target = project_id
    else:
        raise ValueError(f"不支持的 library_type: {library_type}")

    try:
        session = get_session_by_target(target)
    except (ValueError, FileNotFoundError):
        session = DatabaseSession()

    features = b""
    try:
        img_id = int(img_id_or_path)
        with session:
            features = get_image_features_by_id(session, img_id)
        if not features:
            return []
        features = np.frombuffer(features, dtype=np.float32).reshape(1, -1)
    except ValueError:
        img_path = img_id_or_path
        features = process_image(img_path)

    with session:
        results = search_video_by_feature(features, None, threshold, None, filter_path, start_time, end_time, session=session)

    # 添加来源标注
    source_label = _get_source_label(library_type, project_id)
    for result in results:
        result['source'] = source_label

    return results


def search_pexels_video_by_feature(positive_feature, positive_threshold=POSITIVE_THRESHOLD):
    """
    通过特征搜索pexels视频
    :param positive_feature: np.array, 正向特征向量
    :param positive_threshold: int/float, 正向阈值
    :return: list, 搜索结果列表
    """
    t0 = time.time()
    with DatabaseSessionPexelsVideo() as session:
        thumbnail_feature_list, thumbnail_loc_list, content_loc_list, \
            title_list, description_list, duration_list, view_count_list = get_pexels_video_features(session)
    if len(thumbnail_feature_list) == 0:  # 没有素材，直接返回空
        return []
    thumbnail_features = np.frombuffer(b"".join(thumbnail_feature_list), dtype=np.float32).reshape(len(thumbnail_feature_list), -1)
    thumbnail_scores = match_batch(positive_feature, None, thumbnail_features, positive_threshold, None)
    return_list = []
    for score, thumbnail_loc, content_loc, title, description, duration, view_count in zip(
            thumbnail_scores, thumbnail_loc_list, content_loc_list,
            title_list, description_list, duration_list, view_count_list
    ):
        if not score:
            continue
        return_list.append({
            "thumbnail_loc": thumbnail_loc,
            "content_loc": content_loc,
            "title": title,
            "description": description,
            "duration": duration,
            "view_count": view_count,
            "score": float(score),
        })
    return_list = sorted(return_list, key=lambda x: x["score"], reverse=True)
    logger.info("查询使用时间：%.2f" % (time.time() - t0))
    return return_list


@lru_cache(maxsize=CACHE_SIZE)
def search_pexels_video_by_text(positive_prompt: str, positive_threshold=POSITIVE_THRESHOLD):
    """
    通过文字搜索pexels视频
    :param positive_prompt: 正向提示词
    :param positive_threshold: int/float, 正向阈值
    :return:
    """
    positive_feature = process_text(positive_prompt)
    return search_pexels_video_by_feature(positive_feature, positive_threshold)


if __name__ == '__main__':
    import argparse
    from utils import format_seconds

    parser = argparse.ArgumentParser(description='Search local photos and videos through natural language.')
    parser.add_argument('search_type', metavar='<type>', choices=['image', 'video'], help='search type (image or video).')
    parser.add_argument('positive_prompt', metavar='<positive_prompt>')
    args = parser.parse_args()
    positive_prompt = args.positive_prompt
    if args.search_type == 'image':
        results = search_image_by_text_path_time(positive_prompt)
        print(positive_prompt)
        print(f'results count: {len(results)}')
        print('-' * 30)
        for item in results[:5]:
            print(f'path  : {item["path"]}')
            print(f'score: {item["score"]:.3f}')
            print('-' * 30)
    elif args.search_type == 'video':
        results = search_video_by_text_path_time(positive_prompt)
        print(positive_prompt)
        print(f'results count: {len(results)}')
        print('-' * 30)
        for item in results[:5]:
            start_time = format_seconds(item["start_time"])
            end_time = format_seconds(item["end_time"])
            print(f'path  : {item["path"]}')
            print(f'range: {start_time} ~ {end_time}')
            print(f'score: {item["score"]:.3f}')
            print('-' * 30)
