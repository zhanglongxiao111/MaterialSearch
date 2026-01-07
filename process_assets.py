# 预处理图片和视频，建立索引，加快搜索速度
import logging
import traceback

import cv2
import numpy as np
import requests
import torch.cuda
from PIL import Image
from tqdm import trange
from transformers import AutoModelForZeroShotImageClassification, AutoProcessor

from config import *
from utils_image import extract_rhino_preview

logger = logging.getLogger(__name__)

logger.info("Loading model...")
model = AutoModelForZeroShotImageClassification.from_pretrained(MODEL_NAME).to(DEVICE)
processor = AutoProcessor.from_pretrained(MODEL_NAME)
logger.info("Model loaded.")


def get_image_feature(images):
    """
    :param images: 图片列表
    :return: feature
    """
    if images is None or len(images) == 0:
        return None
    features = None
    try:
        inputs = processor(images=images, return_tensors="pt")["pixel_values"].to(DEVICE)
        features = model.get_image_features(inputs)
        normalized_features = features / torch.norm(features, dim=1, keepdim=True)  # 归一化，方便后续计算余弦相似度
        features = normalized_features.detach().cpu().numpy()
    except Exception as e:
        logger.exception("处理图片报错：type=%s error=%s" % (type(images), repr(e)))
        traceback.print_stack()
        if type(images) == list:
            print("images[0]:", images[0])
        else:
            print("images:", images)
        if features is not None:
            print("feature.shape:", features.shape)
            print("feature:", features)
        # 如果报错内容包含 not enough GPU video memory，就打印额外的日志
        if "not enough GPU video memory" in repr(e) and MODEL_NAME != "OFA-Sys/chinese-clip-vit-base-patch16":
            logger.error("显存不足，请使用小模型（OFA-Sys/chinese-clip-vit-base-patch16）！！！")
    return features


def get_image_data(path: str, ignore_small_images: bool = True):
    """
    获取图片像素数据，如果出错返回 None
    :param path: string, 图片路径
    :param ignore_small_images: bool, 是否忽略尺寸过小的图片
    :return: <class 'numpy.nparray'>, 图片数据，如果出错返回 None
    """
    try:
        if path.lower().endswith('.3dm'):
            image = extract_rhino_preview(path)
            if image is None:
                return None
        else:
            image = Image.open(path)

        if ignore_small_images:
            width, height = image.size
            if width < IMAGE_MIN_WIDTH or height < IMAGE_MIN_HEIGHT:
                return None
                # processor 中也会这样预处理 Image
        # 在这里提前转为 np.array 避免到时候抛出异常
        image = image.convert('RGB')
        image = np.array(image)
        return image
    except Exception as e:
        logger.exception("打开图片报错：path=%s error=%s" % (path, repr(e)))
        traceback.print_stack()
        return None


def process_image(path, ignore_small_images=True):
    """
    处理图片，返回图片特征
    :param path: string, 图片路径
    :param ignore_small_images: bool, 是否忽略尺寸过小的图片
    :return: <class 'numpy.nparray'>, 图片特征
    """
    image = get_image_data(path, ignore_small_images)
    if image is None:
        return None
    feature = get_image_feature(image)
    return feature


def process_images(path_list, ignore_small_images=True):
    """
    处理图片，返回图片特征
    :param path_list: string, 图片路径列表
    :param ignore_small_images: bool, 是否忽略尺寸过小的图片
    :return: <class 'numpy.nparray'>, 图片特征
    """
    images = []
    for path in path_list.copy():
        image = get_image_data(path, ignore_small_images)
        if image is None:
            path_list.remove(path)
            continue
        images.append(image)
    if not images:
        return None, None
    feature = get_image_feature(images)
    if torch.cuda.is_available() and LOW_CUDA_MEM:
        torch.cuda.empty_cache()
    return path_list, feature


def process_web_image(url):
    """
    处理网络图片，返回图片特征
    :param url: string, 图片URL
    :return: <class 'numpy.nparray'>, 图片特征
    """
    try:
        image = Image.open(requests.get(url, stream=True).raw)
    except Exception as e:
        logger.warning("获取图片报错：%s %s" % (url, repr(e)))
        return None
    feature = get_image_feature(image)
    return feature


def get_frames(video: cv2.VideoCapture):
    """ 
    获取视频的帧数据
    :return: (list[int], list[array]) (帧编号列表, 帧像素数据列表) 元组
    """
    frame_rate = round(video.get(cv2.CAP_PROP_FPS))
    total_frames = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
    logger.debug(f"fps: {frame_rate} total: {total_frames}")
    ids, frames = [], []
    for current_frame in trange(
            0, total_frames, FRAME_INTERVAL * frame_rate, desc="当前进度", unit="frame"
    ):
        # 在 FRAME_INTERVAL 为 2（默认值），frame_rate 为 24
        # 即 FRAME_INTERVAL * frame_rate == 48 时测试
        # 直接设置当前帧的运行效率低于使用 grab 跳帧
        # 如果需要跳的帧足够多，也许直接设置效率更高
        # video.set(cv2.CAP_PROP_POS_FRAMES, current_frame)
        ret, frame = video.read()
        if not ret:
            break
        ids.append(current_frame // frame_rate)
        frames.append(frame)
        if len(frames) == SCAN_PROCESS_BATCH_SIZE:
            yield ids, frames
            ids = []
            frames = []
        for _ in range(FRAME_INTERVAL * frame_rate - 1):
            video.grab()  # 跳帧
    yield ids, frames


def process_video(path):
    """
    处理视频并返回处理完成的数据
    返回一个生成器，每调用一次则返回视频下一个帧的数据
    :param path: string, 视频路径
    :return: [int, <class 'numpy.nparray'>], [当前是第几帧（被采集的才算），图片特征]
    """
    logger.info(f"处理视频中：{path}")
    video = None
    try:
        video = cv2.VideoCapture(path)
        for ids, frames in get_frames(video):
            if not frames:
                continue
            features = get_image_feature(frames)
            if features is None:
                logger.warning("features is None in process_video")
                continue
            for id, feature in zip(ids, features):
                yield id, feature
    except Exception as e:
        logger.exception("处理视频报错：path=%s error=%s" % (path, repr(e)))
        traceback.print_stack()
        if video is not None:
            frame_rate = round(video.get(cv2.CAP_PROP_FPS))
            total_frames = video.get(cv2.CAP_PROP_FRAME_COUNT)
            print(f"fps: {frame_rate} total: {total_frames}")
            video.release()
        return
    finally:
        if torch.cuda.is_available() and LOW_CUDA_MEM:
            torch.cuda.empty_cache()


def process_text(input_text):
    """
    预处理文字，返回文字特征
    :param input_text: string, 被处理的字符串
    :return: <class 'numpy.nparray'>,  文字特征
    """
    feature = None
    if not input_text:
        return None
    try:
        text = processor(text=input_text, return_tensors="pt", padding=True)["input_ids"].to(DEVICE)
        feature = model.get_text_features(text)
        normalize_feature = feature / torch.norm(feature, dim=1, keepdim=True)  # 归一化，方便后续计算余弦相似度
        feature = normalize_feature.detach().cpu().numpy()
    except Exception as e:
        logger.exception("处理文字报错：text=%s error=%s" % (input_text, repr(e)))
        traceback.print_stack()
        if feature is not None:
            print("feature.shape:", feature.shape)
            print("feature:", feature)
    return feature


def match_text_and_image(text_feature, image_feature):
    """
    匹配文字和图片，返回余弦相似度
    :param text_feature: <class 'numpy.nparray'>, 文字特征
    :param image_feature: <class 'numpy.nparray'>, 图片特征
    :return: <class 'numpy.nparray'>, 文字和图片的余弦相似度，shape=(1, 1)
    """
    score = image_feature @ text_feature.T
    return score


def match_batch(
        positive_feature,
        negative_feature,
        image_features,
        positive_threshold,
        negative_threshold,
):
    """
    匹配image_feature列表并返回余弦相似度
    :param positive_feature: <class 'numpy.ndarray'>, 正向提示词特征，shape=(1, m)
    :param negative_feature: <class 'numpy.ndarray'>, 反向提示词特征，shape=(1, m)
    :param image_features: <class 'numpy.ndarray'>, 图片特征，shape=(n, m)
    :param positive_threshold: int/float, 正向提示分数阈值，高于此分数才显示
    :param negative_threshold: int/float, 反向提示分数阈值，低于此分数才显示
    :return: <class 'numpy.nparray'>, 提示词和每个图片余弦相似度列表，shape=(n, )，如果小于正向提示分数阈值或大于反向提示分数阈值则会置0
    """
    if positive_feature is None:  # 没有正向feature就把分数全部设成1
        positive_scores = np.ones(len(image_features))
    else:
        positive_scores = image_features @ positive_feature.T
    if negative_feature is not None:
        negative_scores = image_features @ negative_feature.T
    # 根据阈值进行过滤
    scores = np.where(positive_scores < positive_threshold / 100, 0, positive_scores)
    if negative_feature is not None:
        scores = np.where(negative_scores > negative_threshold / 100, 0, scores)
    # 确保返回 1D 分数向量（即便只有一条记录也能被 zip 正常迭代）
    return np.asarray(scores).reshape(-1)


# ==================== PDF 处理 ====================

def get_pdf_page_count(file_path: str):
    """
    获取 PDF 页数，无法获取时返回 None。
    :param file_path: PDF 文件路径
    :return: int or None
    """
    try:
        from pdf2image import pdfinfo_from_path
    except ImportError:
        return None
    try:
        kwargs = {}
        if PDF_POPPLER_PATH:
            kwargs["poppler_path"] = PDF_POPPLER_PATH
        info = pdfinfo_from_path(file_path, **kwargs)
        pages = info.get("Pages") or info.get("pages")
        return int(pages) if pages is not None else None
    except Exception as exc:
        logger.warning(f"读取 PDF 页数失败 {file_path}: {exc}")
        return None


def render_pdf_pages(file_path: str, first_page: int, last_page: int, timeout: int = None):
    """
    渲染 PDF 指定页码，返回 PIL Image 列表。
    :param file_path: PDF 文件路径
    :param first_page: 起始页（从 1 开始）
    :param last_page: 结束页
    :param timeout: 超时时间（秒），None 表示不限制
    :return: list[PIL.Image] 或 None（失败时）
    :raises: RuntimeError（缺少依赖）, TimeoutError（超时）
    """
    try:
        from pdf2image import convert_from_path
    except ImportError:
        raise RuntimeError("缺少 pdf2image 依赖")

    from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError

    def _convert():
        kwargs = {"first_page": first_page, "last_page": last_page, "dpi": 300}
        if PDF_POPPLER_PATH:
            kwargs["poppler_path"] = PDF_POPPLER_PATH
        return convert_from_path(file_path, **kwargs)

    if timeout:
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(_convert)
            try:
                return future.result(timeout=timeout)
            except FuturesTimeoutError:
                raise TimeoutError(f"PDF 渲染超时（{timeout}s）")
    else:
        return _convert()


def resize_pdf_image(img, target_width: int):
    """
    将 PDF 页面缩放到指定宽度（等比）。
    :param img: PIL.Image
    :param target_width: 目标宽度
    :return: PIL.Image
    """
    if target_width and img.width != target_width:
        ratio = target_width / float(img.width)
        new_height = max(1, int(img.height * ratio))
        img = img.resize((target_width, new_height), Image.Resampling.LANCZOS)
    return img


def save_pdf_page_image(img, file_path: str, page_no: int, mtime: float, cache_dir: str) -> str:
    """
    将渲染后的页面写入缓存目录并返回路径。
    :param img: PIL.Image
    :param file_path: 原始 PDF 路径
    :param page_no: 页码
    :param mtime: 文件修改时间戳
    :param cache_dir: 缓存目录
    :return: 保存的文件路径
    """
    import hashlib
    import os
    os.makedirs(cache_dir, exist_ok=True)
    key_src = f"{file_path}_{mtime}_{page_no}".encode("utf-8", "ignore")
    cache_key = hashlib.sha1(key_src).hexdigest()
    output_path = os.path.join(cache_dir, f"{cache_key}_p{page_no}.jpg")
    img.save(output_path, 'JPEG', quality=90)
    return output_path


def process_pdf_pages(file_path: str, max_pages: int = None, render_width: int = None,
                      timeout: int = None, cache_dir: str = None):
    """
    处理 PDF 文件，渲染页面并提取特征。
    
    :param file_path: PDF 文件路径
    :param max_pages: 最大处理页数，默认使用 PDF_MAX_PAGES
    :param render_width: 渲染宽度，默认使用 PDF_RENDER_WIDTH
    :param timeout: 渲染超时时间，默认使用 PDF_RENDER_TIMEOUT
    :param cache_dir: 缓存目录，默认使用 TEMP_PATH/pdf_pages
    :return: generator，每次 yield 一个字典：
             {
                 'page_no': int,
                 'page_count': int,
                 'is_primary': bool,
                 'pages_truncated': bool,
                 'width': int,
                 'height': int,
                 'thumbnail_path': str,
                 'feature': np.ndarray or None,
                 'error': str or None
             }
    :raises: RuntimeError（依赖缺失）, TimeoutError（渲染超时）
    """
    import os
    
    # 使用默认配置
    if max_pages is None:
        max_pages = PDF_MAX_PAGES
    if render_width is None:
        render_width = PDF_RENDER_WIDTH
    if timeout is None:
        timeout = PDF_RENDER_TIMEOUT
    if cache_dir is None:
        cache_dir = os.path.join(TEMP_PATH, 'pdf_pages')

    # 获取页数
    page_count = get_pdf_page_count(file_path)
    last_page = min(page_count or max_pages, max_pages)
    
    # 渲染页面
    images = render_pdf_pages(file_path, 1, last_page, timeout)
    if not images:
        return

    pages_truncated = bool(page_count and page_count > max_pages)
    total_pages = page_count or len(images)
    mtime = os.path.getmtime(file_path)

    for idx, img in enumerate(images, start=1):
        result = {
            'page_no': idx,
            'page_count': total_pages,
            'is_primary': (idx == 1),
            'pages_truncated': pages_truncated,
            'width': None,
            'height': None,
            'thumbnail_path': None,
            'feature': None,
            'error': None
        }
        
        try:
            img_rgb = img.convert('RGB')
            img_resized = resize_pdf_image(img_rgb, render_width)
            result['width'] = img_resized.width
            result['height'] = img_resized.height

            # 保存缩略图
            thumb_path = save_pdf_page_image(img_resized, file_path, idx, mtime, cache_dir)
            result['thumbnail_path'] = thumb_path

            # 提取特征
            feature = process_image(thumb_path, ignore_small_images=False)
            if feature is None:
                result['error'] = '特征提取失败'
                logger.warning(f"PDF 页面特征提取失败: {file_path}#p{idx}")
            else:
                result['feature'] = feature
        except Exception as exc:
            result['error'] = str(exc)
            logger.error(f"处理 PDF 页面失败 {file_path}#p{idx}: {exc}")

        yield result
