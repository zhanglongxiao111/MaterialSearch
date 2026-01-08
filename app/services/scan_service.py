"""
扫描服务

封装素材扫描业务逻辑。
"""
import datetime
import logging
import os
import pickle
import threading
import time
from pathlib import Path

from config import *
from app.integrations.sqlite_manager import (
    get_image_count,
    get_video_count,
    get_video_frame_count,
    delete_record_if_not_exist,
    delete_image_if_outdated,
    delete_video_if_outdated,
    delete_pdf_if_outdated,
    add_video,
    add_image,
    get_session_by_target,
    get_db_manager,
    add_pdf_page,
    delete_pdf_pages_by_path,
)
from models import create_tables, DatabaseSession
from app.services.asset_service import process_images, process_video, process_image, process_pdf_pages
from app.services.search_service import clean_cache
from app.utils.common import get_file_hash
from app.utils.image import calculate_image_properties

scanning = False
status = {}


class Scanner:
    """
    扫描类
    """

    def __init__(self) -> None:
        # 全局变量
        self.scanned = False  # 表示本次自动扫描时间段内是否以及扫描过
        self.is_scanning = False
        self.scan_start_time = 0
        self.scanning_files = 0
        self.total_images = 0
        self.total_videos = 0
        self.total_video_frames = 0
        self.scanned_files = 0
        self.is_continue_scan = False
        self.logger = logging.getLogger(__name__)
        self.temp_file = f"{TEMP_PATH}/assets.pickle"
        self.assets = dict()

        # 自动扫描时间
        self.start_time = datetime.time(*AUTO_SCAN_START_TIME)
        self.end_time = datetime.time(*AUTO_SCAN_END_TIME)
        self.is_cross_day = self.start_time > self.end_time  # 是否跨日期

        # 处理跳过路径
        self.skip_paths = [Path(i) for i in SKIP_PATH if i]
        self.ignore_keywords = [i for i in IGNORE_STRINGS if i]
        self.extensions = IMAGE_EXTENSIONS + VIDEO_EXTENSIONS + PDF_EXTENSIONS

    def init(self):
        create_tables()
        with DatabaseSession() as session:
            self.total_images = get_image_count(session)
            self.total_videos = get_video_count(session)
            self.total_video_frames = get_video_frame_count(session)

    def get_status(self):
        """
        获取扫描状态信息
        :return: dict, 状态信息字典
        """
        if self.scanned_files:
            remain_time = (
                    (time.time() - self.scan_start_time)
                    / self.scanned_files
                    * self.scanning_files
            )
        else:
            remain_time = 0
        if self.is_scanning and self.scanning_files != 0:
            progress = self.scanned_files / self.scanning_files
        else:
            progress = 0
        result = {
            "status": self.is_scanning,
            "total_images": self.total_images,
            "total_videos": self.total_videos,
            "total_video_frames": self.total_video_frames,
            "scanning_files": self.scanning_files,
            "remain_files": self.scanning_files - self.scanned_files,
            "progress": progress,
            "remain_time": int(remain_time),
            "enable_login": ENABLE_LOGIN,
        }
        global status
        status = result
        return result

    def save_assets(self):
        with open(self.temp_file, "wb") as f:
            pickle.dump(self.assets, f)

    def filter_path(self, path) -> bool:
        """
        过滤跳过的路径
        """
        if type(path) == str:
            path = Path(path)
        wrong_ext = path.suffix.lower() not in self.extensions
        skip = any((path.is_relative_to(p) for p in self.skip_paths))
        ignore = any((keyword in str(path).lower() for keyword in self.ignore_keywords))
        self.logger.debug(f"{path} 不匹配后缀：{wrong_ext} 跳过：{skip} 忽略：{ignore}")
        return not any((wrong_ext, skip, ignore))

    def generate_or_load_assets(self, scan_paths=None):
        """
        若无缓存文件，扫描目录到self.assets, 并生成新的缓存文件；
        否则加载缓存文件到self.assets
        :param scan_paths: 自定义扫描路径列表，如果为None则使用环境变量 ASSETS_PATH
        :return: None
        """
        if os.path.isfile(self.temp_file):
            self.logger.info("读取上次的目录缓存")
            self.is_continue_scan = True
            with open(self.temp_file, "rb") as f:
                self.assets = pickle.load(f)
        else:
            self.is_continue_scan = False
            self.scan_dir(scan_paths)
            self.save_assets()

    def is_current_auto_scan_time(self) -> bool:
        """
        判断当前时间是否在自动扫描时间段内
        :return: 当前时间是否在自动扫描时间段内时返回True，否则返回False
        """
        current_time = datetime.datetime.now().time()
        is_in_range = (
                self.start_time <= current_time < self.end_time
        )  # 当前时间是否在 start_time 与 end_time 区间内
        return self.is_cross_day ^ is_in_range  # 跨日期与在区间内异或时，在自动扫描时间内

    def auto_scan(self):
        """
        自动扫描，每5秒判断一次时间，如果在目标时间段内则开始扫描。
        :return: None
        """
        while True:
            time.sleep(5)
            if self.is_scanning:
                self.scanned = True  # 设置扫描标记，这样如果手动扫描在自动扫描时间段内结束，也不会重新扫描
            elif not self.is_current_auto_scan_time():
                self.scanned = False  # 已经过了自动扫描时间段，重置扫描标记
            elif not self.scanned and self.is_current_auto_scan_time():
                self.logger.info("触发自动扫描")
                self.scanned = True  # 表示本目标时间段内已进行扫描，防止同个时间段内扫描多次
                self.scan(True)

    def scan_dir(self, scan_paths=None):
        """
        遍历文件并将符合条件的文件加入 assets 集合
        :param scan_paths: 自定义扫描路径列表，如果为None则使用环境变量 ASSETS_PATH
        """
        self.generate_assets_from_paths(scan_paths)

    def generate_assets_from_paths(self, paths=None):
        """
        从指定路径生成assets字典，把所有符合要求的素材文件路径存入assets字典
        :param paths: 路径列表，如果为None则使用环境变量 ASSETS_PATH
        """
        self.assets = dict()
        if paths is None:
            paths = [Path(i) for i in ASSETS_PATH if i]
        else:
            # 确保路径是 Path 对象，并过滤掉空字符串
            paths = [Path(p) for p in paths if p and p.strip()]
        # 遍历根目录及其子目录下的所有文件
        for path in paths:
            if not path.exists():
                self.logger.warning(f"路径不存在，跳过: {path}")
                continue
            for file in filter(self.filter_path, path.rglob("*")):
                modify_time = os.path.getmtime(str(file))
                try:  # 尝试把modify_time转换成datetime用来写入数据库
                    modify_time = datetime.datetime.fromtimestamp(modify_time)
                except Exception as e:  # 如果无法转换修改日期，则改为checksum
                    self.logger.warning("文件修改日期有问题：", str(file), modify_time, "导致datetime转换报错", repr(e))
                    modify_time = None
                self.assets[str(file)] = modify_time

    def handle_image_batch(self, session, image_batch_dict):
        path_list, features_list = process_images(list(image_batch_dict.keys()))
        if not path_list or features_list is None:
            return
        for path, features in zip(path_list, features_list):
            # 写入数据库
            features = features.tobytes()
            modify_time, checksum = image_batch_dict[path]

            # 计算图片属性
            props = calculate_image_properties(path)
            if props:
                add_image(session, path, modify_time, checksum, features,
                         width=props.get('width'),
                         height=props.get('height'),
                         aspect_ratio=props.get('aspect_ratio'),
                         aspect_ratio_standard=props.get('aspect_ratio_standard'),
                         file_size=props.get('file_size'),
                         file_format=props.get('file_format'),
                         phash=props.get('phash'))
            else:
                # 如果属性计算失败，仍然添加图片（只是没有扩展属性）
                add_image(session, path, modify_time, checksum, features)

            del self.assets[path]
        self.total_images = get_image_count(session)

    def handle_pdf(self, session, file_path, modify_time, checksum):
        """处理单个 PDF 文件：渲染页面、提取特征、写入数据库"""
        try:
            # 删除旧记录
            delete_pdf_pages_by_path(session, file_path)
            
            saved_pages = 0
            file_size = os.path.getsize(file_path)
            
            for page_result in process_pdf_pages(file_path):
                if page_result['error']:
                    self.logger.warning(f"PDF 页面处理失败: {file_path}#p{page_result['page_no']}: {page_result['error']}")
                    continue
                
                add_pdf_page(
                    session,
                    source_path=file_path,
                    page_no=page_result['page_no'],
                    page_count=page_result['page_count'],
                    is_primary=page_result['is_primary'],
                    pages_truncated=page_result['pages_truncated'],
                    modify_time=modify_time,
                    checksum=checksum,
                    features=page_result['feature'].tobytes(),
                    width=page_result['width'],
                    height=page_result['height'],
                    file_size=file_size,
                    thumbnail_path=page_result['thumbnail_path']
                )
                saved_pages += 1
            
            if saved_pages:
                self.logger.info(f"已索引 PDF: {file_path} ({saved_pages} 页)")
            else:
                self.logger.warning(f"PDF 索引失败（无有效页面）: {file_path}")
                
        except RuntimeError as dep_err:
            self.logger.warning(f"缺少 PDF 依赖，跳过: {file_path} - {dep_err}")
        except TimeoutError as timeout_err:
            self.logger.error(f"PDF 渲染超时: {file_path} - {timeout_err}")
        except Exception as exc:
            self.logger.error(f"处理 PDF 失败 {file_path}: {exc}")

    def scan(self, auto=False, target='permanent', scan_paths=None):
        """
        扫描资源。如果存在assets.pickle，则直接读取并开始扫描。如果不存在，则先读取所有文件路径，并写入assets.pickle，然后开始扫描。
        每100个文件重新保存一次assets.pickle，如果程序被中断，下次可以从断点处继续扫描。扫描完成后删除assets.pickle并清缓存。
        :param auto: 是否由AUTO_SCAN触发的
        :param target: 扫描目标库，'permanent' 或 'proj_xxx'
        :param scan_paths: 自定义扫描路径列表，如果为None则使用环境变量 ASSETS_PATH
        """
        global scanning
        self.logger.info(f"开始扫描 (目标库: {target})")
        self.is_scanning = True
        scanning = True
        self.scan_start_time = time.time()

        # 为不同库使用不同的缓存文件
        self.temp_file = f"{TEMP_PATH}/assets_{target}.pickle"
        self.logger.info(f"使用缓存文件: {self.temp_file}")

        self.generate_or_load_assets(scan_paths)

        # 根据目标获取对应的 session
        try:
            session = get_session_by_target(target)
        except (ValueError, FileNotFoundError) as e:
            self.logger.error(f"无法获取目标库 session: {e}")
            self.is_scanning = False
            raise

        try:
            with session:
                # 删除不存在的文件记录
                if not self.is_continue_scan:  # 非断点恢复的情况下才删除
                    delete_record_if_not_exist(session, set(self.assets.keys()))
                # 将没有变化的文件从assets中移除(不启用checksum的时候直接检查，如果启用，这个会很慢，留到正式扫描再检查)
                if not ENABLE_CHECKSUM:
                    for path in self.assets.copy():
                        modify_time = self.assets[path]
                        # 如果数据库里有这个文件，并且没有发生变化，则跳过
                        if path.lower().endswith(IMAGE_EXTENSIONS):  # 图片
                            not_modified = delete_image_if_outdated(session, path, modify_time)
                            if not_modified:
                                del self.assets[path]
                                continue
                        elif path.lower().endswith(VIDEO_EXTENSIONS):  # 视频
                            not_modified = delete_video_if_outdated(session, path, modify_time)
                            if not_modified:
                                del self.assets[path]
                                continue
                        elif path.lower().endswith(PDF_EXTENSIONS):  # PDF
                            not_modified = delete_pdf_if_outdated(session, path, modify_time)
                            if not_modified:
                                del self.assets[path]
                                continue
                # 扫描文件
                self.scanning_files = len(self.assets)
                image_batch_dict = {}  # 批量处理文件的字典，用字典方便某个图片有问题的时候的处理
                for path in self.assets.copy():
                    self.scanned_files += 1
                    if self.scanned_files % AUTO_SAVE_INTERVAL == 0:  # 每扫描 AUTO_SAVE_INTERVAL 个文件重新save一下
                        self.save_assets()
                    if auto and not self.is_current_auto_scan_time():  # 如果是自动扫描，判断时间自动停止
                        self.logger.info(f"超出自动扫描时间，停止扫描")
                        break
                    # 如果文件不存在，则忽略（扫描时文件被移动或删除则会触发这种情况）
                    if not os.path.isfile(path):
                        continue
                    modify_time = self.assets[path]
                    checksum = None
                    if ENABLE_CHECKSUM or modify_time is None:  # 如果启用checksum则用checksum
                        checksum = get_file_hash(path)
                    # 如果数据库里有这个文件，并且没有发生变化，则跳过，否则进行预处理并入库
                    if path.lower().endswith(IMAGE_EXTENSIONS):  # 图片
                        not_modified = delete_image_if_outdated(session, path, modify_time, checksum)
                        if not_modified:
                            del self.assets[path]
                            continue
                        image_batch_dict[path] = (modify_time, checksum)
                        # 达到SCAN_PROCESS_BATCH_SIZE再进行批量处理
                        if len(image_batch_dict) == SCAN_PROCESS_BATCH_SIZE:
                            self.handle_image_batch(session, image_batch_dict)
                            image_batch_dict = {}
                        continue
                    elif path.lower().endswith(VIDEO_EXTENSIONS):  # 视频
                        not_modified = delete_video_if_outdated(session, path, modify_time, checksum)
                        if not_modified:
                            del self.assets[path]
                            continue
                        add_video(session, path, modify_time, checksum, process_video(path))
                        self.total_video_frames = get_video_frame_count(session)
                        self.total_videos = get_video_count(session)
                    elif path.lower().endswith(PDF_EXTENSIONS):  # PDF
                        not_modified = delete_pdf_if_outdated(session, path, modify_time, checksum)
                        if not_modified:
                            del self.assets[path]
                            continue
                        self.handle_pdf(session, path, modify_time, checksum)
                    del self.assets[path]
                if len(image_batch_dict) != 0:  # 最后如果图片数量没达到SCAN_PROCESS_BATCH_SIZE，也进行一次处理
                    self.handle_image_batch(session, image_batch_dict)
                # 最后重新统计一下数量
                self.total_images = get_image_count(session)
                self.total_videos = get_video_count(session)
                self.total_video_frames = get_video_frame_count(session)

            # 扫描完成后，如果是项目库，更新项目统计
            if target.startswith('proj_'):
                try:
                    from app.services.project_service import get_project_manager
                    pm = get_project_manager()
                    pm.update_project_stats(target)
                    self.logger.info(f"已更新项目统计: {target}")
                except Exception as e:
                    self.logger.warning(f"更新项目统计失败: {e}")

        finally:
            self.scanning_files = 0
            self.scanned_files = 0
            if os.path.exists(self.temp_file):
                os.remove(self.temp_file)
            self.logger.info("扫描完成，用时%d秒" % int(time.time() - self.scan_start_time))
            clean_cache()  # 清空搜索缓存
            self.is_scanning = False
            scanning = False


scanner = Scanner()


class ScanService:
    """
    扫描服务类

    对 Scanner 进行封装，提供更清晰的调用接口。
    """

    def __init__(self):
        self._scanner = scanner

    @property
    def is_scanning(self) -> bool:
        return self._scanner.is_scanning

    def get_status(self):
        return self._scanner.get_status()

    def start_scan(self, target: str = "permanent", paths=None) -> bool:
        if self.is_scanning:
            return False
        if target != "permanent" and not paths:
            return False
        if target.startswith("proj_"):
            from app.services.project_service import get_project_manager
            pm = get_project_manager()
            if not pm.get_project(target):
                return False

        if target != "permanent":
            scan_thread = threading.Thread(
                target=self._scanner.scan,
                args=(False, target, paths),
            )
        else:
            scan_thread = threading.Thread(
                target=self._scanner.scan,
                args=(False, target),
            )
        scan_thread.start()
        return True

    def stop_scan(self) -> bool:
        try:
            self._scanner.stop_scan()
            return True
        except Exception:
            return False


_scan_service = None


def get_scan_service() -> ScanService:
    global _scan_service
    if _scan_service is None:
        _scan_service = ScanService()
    return _scan_service


__all__ = [
    "Scanner",
    "scanner",
    "scanning",
    "status",
    "ScanService",
    "get_scan_service",
]
