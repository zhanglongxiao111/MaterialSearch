"""
扫描服务

封装素材扫描业务逻辑。
"""
import logging
import threading
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


class ScanService:
    """
    扫描服务类
    
    提供素材扫描功能。
    """
    
    def __init__(self):
        from scan import scanner
        self._scanner = scanner
    
    @property
    def is_scanning(self) -> bool:
        """是否正在扫描"""
        return self._scanner.is_scanning
    
    def get_status(self) -> Dict[str, Any]:
        """获取扫描状态"""
        return self._scanner.get_status()
    
    def start_scan(
        self, 
        target: str = 'permanent', 
        paths: Optional[List[str]] = None
    ) -> bool:
        """
        启动扫描任务
        
        Args:
            target: 目标库
            paths: 扫描路径列表（项目库必须指定）
        
        Returns:
            是否成功启动
        """
        if self.is_scanning:
            logger.warning("扫描正在进行中，无法启动新扫描")
            return False
        
        if target != 'permanent' and not paths:
            logger.error("项目库扫描必须指定路径")
            return False
        
        # 验证项目存在
        if target.startswith('proj_'):
            from project_manager import get_project_manager
            pm = get_project_manager()
            project = pm.get_project(target)
            if not project:
                logger.error(f"项目不存在: {target}")
                return False
        
        # 在新线程启动扫描
        if target != 'permanent':
            scan_thread = threading.Thread(
                target=self._scanner.scan,
                args=(False, target, paths)
            )
        else:
            scan_thread = threading.Thread(
                target=self._scanner.scan,
                args=(False, target)
            )
        
        scan_thread.start()
        logger.info(f"扫描任务已启动: target={target}")
        return True
    
    def stop_scan(self) -> bool:
        """
        停止扫描任务
        
        Returns:
            是否成功停止
        """
        try:
            self._scanner.stop_scan()
            logger.info("扫描任务已停止")
            return True
        except Exception as e:
            logger.error(f"停止扫描失败: {e}")
            return False


# 单例实例
_scan_service: Optional[ScanService] = None


def get_scan_service() -> ScanService:
    """获取扫描服务实例"""
    global _scan_service
    if _scan_service is None:
        _scan_service = ScanService()
    return _scan_service
