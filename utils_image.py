"""
图片属性计算工具
用于计算图片的宽高比、标准比例、文件格式、感知哈希等
"""

import os
import logging
import imagehash
import io
import sys
import mmap
import struct
import zlib
import hashlib
from pathlib import Path
from PIL import Image
from typing import Dict, Optional

# Windows Shell 提取依赖
if sys.platform == 'win32':
    try:
        from ctypes import POINTER, byref, cast, windll, c_void_p, c_wchar_p
        from ctypes.wintypes import SIZE, UINT, HANDLE, HBITMAP
        from comtypes import GUID, IUnknown, COMMETHOD, HRESULT
        import win32gui
        import win32ui
        import pythoncom
        
        # 定义 IShellItemImageFactory 接口
        class IShellItemImageFactory(IUnknown):
            _case_insensitive_ = True
            _iid_ = GUID('{BCC18B79-BA16-442f-80c4-8A59C30C463B}')
            _idlflags_ = []
            _methods_ = [
                COMMETHOD([], HRESULT, 'GetImage',
                        (['in'], SIZE, 'size'),
                        (['in'], UINT, 'flags'),
                        (['out'], POINTER(HBITMAP), 'phbm')),
            ]
        
        HAS_SHELL_EXT = True
    except ImportError:
        HAS_SHELL_EXT = False
else:
    HAS_SHELL_EXT = False

PNG_SIGNATURE = b'\x89PNG\r\n\x1a\n'
BMP_SIGNATURE = b'BM'
# Rhino 压缩预览块标记 (TCODE_PROPERTIES_COMPRESSED_PREVIEWIMAGE)
RHINO_PREVIEW_SIG = b'\x25\x80\x00\x20'

RHINO_PREVIEW_CACHE = Path(__file__).resolve().parent / "rhino_preview_cache"

logger = logging.getLogger(__name__)


def get_standard_aspect_ratio(ratio: float) -> str:
    """
    获取标准宽高比

    Args:
        ratio: 实际宽高比

    Returns:
        str: 标准宽高比字符串
    """
    standard_ratios = {
        1.0: "1:1",
        1.333: "4:3",
        1.5: "3:2",
        1.6: "16:10",
        1.778: "16:9",
        2.0: "2:1",
        2.333: "21:9",
        0.75: "3:4",
        0.667: "2:3",
        0.5625: "9:16",
    }

    # 找到最接近的标准比例
    min_diff = float('inf')
    result = f"{ratio:.2f}:1"

    for standard_ratio, label in standard_ratios.items():
        diff = abs(ratio - standard_ratio)
        if diff < min_diff:
            min_diff = diff
            result = label

    # 如果差异小于 0.05，认为是标准比例
    if min_diff > 0.05:
        result = f"{ratio:.2f}:1"

    return result


def calculate_image_properties(image_path: str) -> Optional[Dict]:
    """
    计算图片的扩展属性

    Args:
        image_path: 图片路径

    Returns:
        Dict: 图片属性字典，包含：
            - width: 宽度
            - height: 高度
            - aspect_ratio: 宽高比
            - aspect_ratio_standard: 标准宽高比
            - file_size: 文件大小
            - file_format: 文件格式
            - phash: 感知哈希（可选）

        如果失败返回 None
    """
    try:
        if not os.path.exists(image_path):
            return None

        img = None
        if image_path.lower().endswith('.3dm'):
            img = extract_rhino_preview(image_path)
        else:
            img = Image.open(image_path)

        if img is None:
            return None

        try:
            width, height = img.size

            # 跳过太小的图片
            if width < 10 or height < 10:
                return None

            aspect_ratio = round(width / height, 3)
            aspect_ratio_standard = get_standard_aspect_ratio(aspect_ratio)
            file_size = os.path.getsize(image_path)
            
            if image_path.lower().endswith('.3dm'):
                file_format = '3dm'
            else:
                file_format = img.format.lower() if img.format else os.path.splitext(image_path)[1][1:].lower()

            # 计算感知哈希（用于去重）
            try:
                phash = str(imagehash.phash(img))
            except Exception as e:
                logger.warning(f"计算感知哈希失败 {image_path}: {e}")
                phash = None

            return {
                'width': width,
                'height': height,
                'aspect_ratio': aspect_ratio,
                'aspect_ratio_standard': aspect_ratio_standard,
                'file_size': file_size,
                'file_format': file_format,
                'phash': phash,
            }
        finally:
            if hasattr(img, 'close'):
                img.close()

    except Exception as e:
        logger.error(f"计算图片属性失败 {image_path}: {e}")
        return None


def calculate_video_properties(video_path: str) -> Optional[Dict]:
    """
    计算视频的扩展属性

    Args:
        video_path: 视频路径

    Returns:
        Dict: 视频属性字典，包含：
            - width: 宽度
            - height: 高度
            - aspect_ratio: 宽高比
            - duration: 时长（秒）
            - file_size: 文件大小
            - file_format: 文件格式

        如果失败返回 None
    """
    try:
        import cv2

        if not os.path.exists(video_path):
            return None

        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            return None

        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        cap.release()

        duration = int(frame_count / fps) if fps > 0 else 0
        aspect_ratio = round(width / height, 3) if height > 0 else 0
        file_size = os.path.getsize(video_path)
        file_format = os.path.splitext(video_path)[1][1:].lower()

        return {
            'width': width,
            'height': height,
            'aspect_ratio': aspect_ratio,
            'duration': duration,
            'file_size': file_size,
            'file_format': file_format,
        }

    except ImportError:
        logger.warning("cv2 模块未安装，无法计算视频属性")
        return None
    except Exception as e:
        logger.error(f"计算视频属性失败 {video_path}: {e}")
        return None


def extract_rhino_preview(file_path: str) -> Optional[Image.Image]:
    """
    从 Rhino (.3dm) 文件中提取预览图
    优先使用 Windows Shell (IShellItemImageFactory) 提取，失败则回退到二进制扫描。
    缓存落盘以避免重复解析。

    Args:
        file_path: .3dm 文件路径

    Returns:
        PIL.Image 对象或 None
    """
    if not os.path.exists(file_path):
        return None

    # 缓存命中直接返回
    cache_img = _load_cached_preview(file_path)
    if cache_img:
        return cache_img

    # 1. 尝试使用 Windows Shell 提取 (仅限 Windows)
    if HAS_SHELL_EXT:
        try:
            # 必须在当前线程初始化 COM，因为扫描器可能在子线程运行
            pythoncom.CoInitialize()
            
            shell32 = windll.shell32
            h_siif = c_void_p()

            # SHCreateItemFromParsingName
            hr = shell32.SHCreateItemFromParsingName(
                c_wchar_p(file_path),
                c_void_p(0), 
                byref(IShellItemImageFactory._iid_), 
                byref(h_siif)
            )

            if hr == 0:
                siif = cast(h_siif, POINTER(IShellItemImageFactory))
                s = SIZE()
                s.cx = 2048 # 请求 2K 分辨率的缩略图
                s.cy = 2048
                
                # SIIGBF_RESIZETOFIT | SIIGBF_BIGGERSIZEOK | SIIGBF_THUMBNAILONLY
                flags = 0x00000000 | 0x00000001 | 0x00000008
                
                # GetImage 可能抛出 COMError
                try:
                    phbm = siif.GetImage(s, flags)
                    # comtypes 返回处理
                    hbitmap = None
                    if isinstance(phbm, int):
                        hbitmap = phbm
                    else:
                        try:
                            hbitmap = phbm.contents.value
                        except:
                            hbitmap = phbm
                except Exception:
                    hbitmap = None

                if hbitmap:
                    bmi = win32gui.GetObject(hbitmap)
                    width = bmi.bmWidth
                    height = bmi.bmHeight
                    
                    hdcScreen = win32gui.GetDC(0)
                    hdc = win32gui.CreateCompatibleDC(hdcScreen)
                    win32gui.SelectObject(hdc, hbitmap)
                    
                    py_bitmap = win32ui.CreateBitmapFromHandle(hbitmap)
                    bmp_bytes = py_bitmap.GetBitmapBits(True)
                    
                    win32gui.DeleteDC(hdc)
                    win32gui.ReleaseDC(0, hdcScreen)
                    win32gui.DeleteObject(hbitmap)

                    img = None
                    if bmi.bmBitsPixel == 32:
                        img = Image.frombuffer("RGB", (width, height), bmp_bytes, "raw", "BGRX", 0, 1)
                    elif bmi.bmBitsPixel == 24:
                        img = Image.frombuffer("RGB", (width, height), bmp_bytes, "raw", "BGR", 0, 1)
                    
                    if img:
                        _save_cached_preview(file_path, img)
                        return img
        except Exception as e:
            logger.debug(f"Windows Shell 提取失败 {file_path}: {e}")
            # 继续执行后续的二进制扫描
        finally:
            try:
                pythoncom.CoUninitialize()
            except:
                pass

    # 2. 解析 Rhino 压缩预览块 (TCODE_PROPERTIES_COMPRESSED_PREVIEWIMAGE)
    preview = _extract_rhino_preview_from_chunk(file_path)
    if preview:
        _save_cached_preview(file_path, preview)
        return preview

    # 3. 通用签名扫描 (PNG/BMP) - 扫描完整文件避免截断
    preview = _extract_rhino_preview_by_signature(file_path)
    if preview:
        _save_cached_preview(file_path, preview)
    return preview


def _extract_rhino_preview_from_chunk(file_path: str) -> Optional[Image.Image]:
    """
    解析 Rhino 压缩预览块 (0x20008025)，该块存储 zlib 压缩的 DIB 数据。
    """
    try:
        with open(file_path, 'rb') as f, mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mm:
            idx = mm.find(RHINO_PREVIEW_SIG)
            if idx == -1 or idx + 12 > mm.size():
                return None

            length = int.from_bytes(mm[idx + 4: idx + 12], 'little')
            chunk_start = idx + 12
            chunk_end = chunk_start + length

            if length <= 0 or chunk_end > mm.size():
                return None

            chunk = mm[chunk_start:chunk_end]
            compressed_bytes = chunk[:-4] if len(chunk) > 4 else chunk

            dib_data = None
            for wbits in (zlib.MAX_WBITS, -15):
                try:
                    dib_data = zlib.decompress(compressed_bytes, wbits=wbits)
                    break
                except Exception:
                    dib_data = None

            if not dib_data:
                return None

            return _image_from_dib(dib_data)
    except Exception as e:
        logger.debug(f"解析 Rhino 压缩预览失败 {file_path}: {e}")
        return None


def _extract_rhino_preview_by_signature(file_path: str) -> Optional[Image.Image]:
    """
    扫描完整文件寻找 PNG/BMP 签名，作为最后的兜底方案。
    """
    try:
        with open(file_path, 'rb') as f, mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mm:
            # PNG
            png_idx = mm.find(PNG_SIGNATURE)
            if png_idx != -1:
                try:
                    img = Image.open(io.BytesIO(mm[png_idx:]))
                    img.load()
                    return img
                except Exception:
                    pass

            # BMP（可能存在多个，按签名遍历）
            search_start = 0
            while True:
                bmp_idx = mm.find(BMP_SIGNATURE, search_start)
                if bmp_idx == -1 or bmp_idx + 10 > mm.size():
                    break

                file_size = int.from_bytes(mm[bmp_idx + 2:bmp_idx + 6], 'little')
                reserved1 = int.from_bytes(mm[bmp_idx + 6:bmp_idx + 8], 'little')
                reserved2 = int.from_bytes(mm[bmp_idx + 8:bmp_idx + 10], 'little')

                # 校验保留字段与体积，过滤误报
                if reserved1 == 0 and reserved2 == 0 and 1024 < file_size <= mm.size() - bmp_idx:
                    try:
                        img_bytes = mm[bmp_idx:bmp_idx + file_size]
                        img = Image.open(io.BytesIO(img_bytes))
                        img.load()
                        return img
                    except Exception:
                        pass

                search_start = bmp_idx + 1
    except Exception as e:
        logger.debug(f"签名扫描提取失败 {file_path}: {e}")
        return None

    return None


def _image_from_dib(dib_data: bytes) -> Optional[Image.Image]:
    """
    将 DIB 数据包装成 BMP 并加载为 PIL Image。
    """
    if len(dib_data) < 16:
        return None

    try:
        header_size = struct.unpack('<I', dib_data[0:4])[0]
        width = struct.unpack('<I', dib_data[4:8])[0]
        height = struct.unpack('<I', dib_data[8:12])[0]

        if header_size <= 0 or width <= 0 or height == 0:
            return None

        file_size = 14 + len(dib_data)
        pixel_offset = 14 + header_size
        bmp_header = (
            BMP_SIGNATURE
            + struct.pack('<I', file_size)
            + b'\x00\x00\x00\x00'
            + struct.pack('<I', pixel_offset)
        )

        bmp_bytes = bmp_header + dib_data
        img = Image.open(io.BytesIO(bmp_bytes))
        img.load()
        return img
    except Exception:
        return None


def _cache_key(file_path: str) -> str:
    try:
        st = os.stat(file_path)
        key_src = f"{os.path.abspath(file_path)}|{st.st_mtime_ns}|{st.st_size}".encode("utf-8", "ignore")
        return hashlib.sha1(key_src).hexdigest()
    except Exception as e:
        logger.debug(f"生成缓存 key 失败 {file_path}: {e}")
        return ""


def _load_cached_preview(file_path: str) -> Optional[Image.Image]:
    key = _cache_key(file_path)
    if not key:
        return None

    cache_path = RHINO_PREVIEW_CACHE / f"{key}.jpg"
    if not cache_path.exists():
        return None

    try:
        with Image.open(cache_path) as img:
            img.load()
            return img.copy()
    except Exception as e:
        logger.debug(f"读取缓存预览失败 {cache_path}: {e}")
        return None


def _save_cached_preview(file_path: str, img: Image.Image) -> None:
    key = _cache_key(file_path)
    if not key:
        return

    try:
        RHINO_PREVIEW_CACHE.mkdir(parents=True, exist_ok=True)
        cache_path = RHINO_PREVIEW_CACHE / f"{key}.jpg"
        tmp_path = cache_path.with_suffix(".jpg.tmp")

        # 统一转 RGB 再写，避免透明度问题
        to_save = img.convert("RGB")
        to_save.save(tmp_path, format="JPEG", quality=90)
        os.replace(tmp_path, cache_path)
    except Exception as e:
        logger.debug(f"写入缓存预览失败 {file_path}: {e}")
