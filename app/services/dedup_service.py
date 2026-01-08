"""
去重服务

后台执行素材去重任务。
"""
import datetime
import json
import logging
import threading
import uuid
from collections import defaultdict
from typing import Dict, List, Optional, Sequence

import numpy as np
from sqlalchemy import or_

from app.integrations.sqlite_manager import get_db_manager
from app.models import Image, DedupJob
from app.services.search_service import clean_cache

logger = logging.getLogger(__name__)

PHASH_HAMMING_THRESHOLD = 5
CLIP_SIMILARITY_THRESHOLD = 0.95
PHASES = ("checksum", "phash", "clip")


class DedupService:
    """后台执行素材去重的服务"""

    def __init__(self):
        self._lock = threading.Lock()
        self._active_job: Optional[str] = None

    def has_running_job(self) -> bool:
        with self._lock:
            return self._active_job is not None

    def start_job(self,
                  library_type: str = "permanent",
                  created_by: Optional[str] = None,
                  include_phash: bool = True,
                  include_clip: bool = True) -> Dict:
        if library_type != "permanent":
            raise ValueError("当前仅支持永久库去重")

        with self._lock:
            if self._active_job is not None:
                raise RuntimeError("已有去重任务在运行")
            job_id = uuid.uuid4().hex
            self._active_job = job_id

        self._create_job_record(job_id, library_type, created_by or "system")

        thread = threading.Thread(
            target=self._run_job,
            args=(job_id, include_phash, include_clip),
            daemon=True
        )
        thread.start()

        return {"job_id": job_id}

    def _create_job_record(self, job_id: str, library_type: str, created_by: str):
        session = get_db_manager().get_permanent_session()
        try:
            job = DedupJob(
                id=job_id,
                library_type=library_type,
                status="pending",
                phase="init",
                progress=0.0,
                created_at=datetime.datetime.utcnow(),
                created_by=created_by
            )
            session.add(job)
            session.commit()
        finally:
            session.close()

    def _update_job(self, job_id: str, **fields):
        session = get_db_manager().get_permanent_session()
        try:
            job = session.query(DedupJob).filter_by(id=job_id).first()
            if not job:
                return
            for key, value in fields.items():
                setattr(job, key, value)
            job.updated_at = datetime.datetime.utcnow()
            session.commit()
        finally:
            session.close()

    def _run_job(self, job_id: str, include_phash: bool, include_clip: bool):
        manager = get_db_manager()
        session = manager.get_permanent_session()
        duplicates_marked = 0
        duplicate_groups = 0
        space_saving = 0
        stage_reports = []
        try:
            self._update_job(job_id, status="running", phase="reset", progress=0.01)
            # 重置标记
            session.query(Image).update({
                Image.is_duplicate: False,
                Image.duplicate_group: None,
                Image.master_image_id: None,
                Image.duplicate_type: None,
                Image.duplicate_confidence: None,
            }, synchronize_session=False)
            session.commit()

            images: List[Image] = (
                session.query(Image)
                .filter(or_(Image.is_deleted.is_(False), Image.is_deleted.is_(None)))
                .all()
            )
            total_images = len(images)
            logger.info("去重任务 %s - 载入 %s 张图片", job_id, total_images)
            self._update_job(job_id, total_scanned=total_images)

            image_map: Dict[int, Image] = {img.id: img for img in images}
            current_group_index = 1

            def next_group_id(stage_name: str) -> str:
                nonlocal current_group_index
                gid = f"{job_id}:{stage_name}:{current_group_index}"
                current_group_index += 1
                return gid

            # 阶段 1：checksum 精确匹配
            self._update_job(job_id, phase="checksum", progress=0.1)
            checksum_groups = self._group_by_checksum(images)
            exact_stats = self._apply_groups(
                session,
                checksum_groups,
                next_group_id,
                stage_name="checksum",
                confidence_provider=lambda master, member: 1.0,
            )
            duplicates_marked += exact_stats["duplicates"]
            duplicate_groups += exact_stats["groups"]
            space_saving += exact_stats["space_saving"]
            stage_reports.append({
                "stage": "checksum",
                "groups": exact_stats["groups"],
                "duplicates": exact_stats["duplicates"],
            })
            self._update_job(job_id, progress=0.33)

            # 阶段 2：phash 视觉相似
            if include_phash:
                self._update_job(job_id, phase="phash", progress=0.4)
                remaining = [img for img in images if not img.duplicate_group]
                phash_groups = self._group_by_phash(remaining)
                phash_stats = self._apply_groups(
                    session,
                    phash_groups,
                    next_group_id,
                    stage_name="phash",
                    confidence_provider=self._phash_confidence,
                )
                duplicates_marked += phash_stats["duplicates"]
                duplicate_groups += phash_stats["groups"]
                space_saving += phash_stats["space_saving"]
                stage_reports.append({
                    "stage": "phash",
                    "groups": phash_stats["groups"],
                    "duplicates": phash_stats["duplicates"],
                })
                self._update_job(job_id, progress=0.66)

            # 阶段 3：CLIP 向量相似
            if include_clip:
                self._update_job(job_id, phase="clip", progress=0.7)
                remaining = [img for img in images if not img.duplicate_group]
                clip_groups = self._group_by_clip(remaining)
                clip_stats = self._apply_groups(
                    session,
                    clip_groups,
                    next_group_id,
                    stage_name="clip",
                    confidence_provider=self._clip_confidence,
                )
                duplicates_marked += clip_stats["duplicates"]
                duplicate_groups += clip_stats["groups"]
                space_saving += clip_stats["space_saving"]
                stage_reports.append({
                    "stage": "clip",
                    "groups": clip_stats["groups"],
                    "duplicates": clip_stats["duplicates"],
                })
                self._update_job(job_id, progress=0.9)

            report_payload = {
                "generated_at": datetime.datetime.utcnow().isoformat(),
                "total_images": total_images,
                "stages": stage_reports,
                "duplicates_marked": duplicates_marked,
                "duplicate_groups": duplicate_groups,
                "space_saving_bytes": space_saving,
            }
            session.commit()
            clean_cache()
            self._update_job(
                job_id,
                status="completed",
                phase="completed",
                progress=1.0,
                completed_at=datetime.datetime.utcnow(),
                duplicate_groups=duplicate_groups,
                duplicates_marked=duplicates_marked,
                space_saving=space_saving,
                report=json.dumps(report_payload, ensure_ascii=False),
            )
        except Exception as exc:
            logger.exception("去重任务 %s 失败: %s", job_id, exc)
            self._update_job(
                job_id,
                status="failed",
                phase="failed",
                progress=1.0,
                error=str(exc),
                completed_at=datetime.datetime.utcnow(),
            )
        finally:
            session.close()
            with self._lock:
                self._active_job = None

    @staticmethod
    def _select_master(images: Sequence[Image]) -> Image:
        def sort_key(item: Image):
            resolution = (item.width or 0) * (item.height or 0)
            size = item.file_size or 0
            mtime = item.modify_time or datetime.datetime.min
            return resolution, size, mtime

        return max(images, key=sort_key)

    def _apply_groups(
            self,
            session,
            grouped_images: List[List[Image]],
            group_id_maker,
            stage_name: str,
            confidence_provider,
    ) -> Dict[str, int]:
        duplicates = 0
        groups = 0
        space_saving = 0

        for images in grouped_images:
            if len(images) < 2:
                continue
            master = self._select_master(images)
            group_id = group_id_maker(stage_name)
            master.duplicate_group = group_id
            master.master_image_id = None
            master.duplicate_type = None
            master.duplicate_confidence = None
            master.is_duplicate = False

            for img in images:
                if img.id == master.id:
                    continue
                img.duplicate_group = group_id
                img.master_image_id = master.id
                img.is_duplicate = True
                img.duplicate_type = stage_name
                img.duplicate_confidence = float(confidence_provider(master, img))
                space_saving += img.file_size or 0
                duplicates += 1

            groups += 1

        if groups:
            session.commit()

        return {
            "duplicates": duplicates,
            "groups": groups,
            "space_saving": space_saving,
        }

    @staticmethod
    def _group_by_checksum(images: Sequence[Image]) -> List[List[Image]]:
        by_checksum = defaultdict(list)
        for img in images:
            if img.checksum:
                by_checksum[img.checksum].append(img)
        return [items for items in by_checksum.values() if len(items) > 1]

    def _group_by_phash(self, images: Sequence[Image]) -> List[List[Image]]:
        buckets: Dict[str, List[Image]] = defaultdict(list)
        for img in images:
            if not img.phash:
                continue
            buckets[img.phash[:4]].append(img)

        grouped: List[List[Image]] = []
        for items in buckets.values():
            if len(items) < 2:
                continue
            grouped.extend(self._union_by_phash(items))
        return grouped

    def _union_by_phash(self, images: Sequence[Image]) -> List[List[Image]]:
        ids = [img.id for img in images]
        parents = {img_id: img_id for img_id in ids}

        def find(x):
            while parents[x] != x:
                parents[x] = parents[parents[x]]
                x = parents[x]
            return x

        def union(a, b):
            ra, rb = find(a), find(b)
            if ra != rb:
                parents[rb] = ra

        phash_values = {}
        for img in images:
            try:
                phash_values[img.id] = int(img.phash, 16)
            except ValueError:
                continue

        img_list = list(phash_values.keys())
        n = len(img_list)
        for i in range(n):
            for j in range(i + 1, n):
                left = phash_values[img_list[i]]
                right = phash_values[img_list[j]]
                distance = (left ^ right).bit_count()
                if distance <= PHASH_HAMMING_THRESHOLD:
                    union(img_list[i], img_list[j])

        clusters: Dict[int, List[Image]] = defaultdict(list)
        image_map = {img.id: img for img in images}
        for img_id in phash_values.keys():
            clusters[find(img_id)].append(image_map[img_id])

        return [cluster for cluster in clusters.values() if len(cluster) > 1]

    def _group_by_clip(self, images: Sequence[Image]) -> List[List[Image]]:
        feature_vectors = []
        image_ids = []
        image_map = {img.id: img for img in images}

        for img in images:
            if not img.features:
                continue
            arr = np.frombuffer(img.features, dtype=np.float32)
            if arr.size == 0:
                continue
            norm = np.linalg.norm(arr)
            if norm == 0:
                continue
            feature_vectors.append(arr / norm)
            image_ids.append(img.id)

        count = len(feature_vectors)
        if count < 2:
            return []

        vectors = np.vstack(feature_vectors)

        parents = {img_id: img_id for img_id in image_ids}

        def find(x):
            while parents[x] != x:
                parents[x] = parents[parents[x]]
                x = parents[x]
            return x

        def union(a, b):
            ra, rb = find(a), find(b)
            if ra != rb:
                parents[rb] = ra

        for i in range(count):
            vec = vectors[i]
            if i + 1 >= count:
                continue
            sims = np.dot(vectors[i + 1:], vec)
            matches = np.where(sims >= CLIP_SIMILARITY_THRESHOLD)[0]
            for offset in matches.tolist():
                j = i + 1 + offset
                union(image_ids[i], image_ids[j])

        clusters: Dict[int, List[Image]] = defaultdict(list)
        for img_id in image_ids:
            clusters[find(img_id)].append(image_map[img_id])

        return [cluster for cluster in clusters.values() if len(cluster) > 1]

    @staticmethod
    def _phash_confidence(master: Image, member: Image) -> float:
        if not master.phash or not member.phash:
            return 0.5
        try:
            a = int(master.phash, 16)
            b = int(member.phash, 16)
        except ValueError:
            return 0.5
        distance = (a ^ b).bit_count()
        max_bits = max(len(master.phash), len(member.phash)) * 4
        similarity = 1 - (distance / max_bits)
        return max(0.0, min(1.0, similarity))

    @staticmethod
    def _clip_confidence(master: Image, member: Image) -> float:
        if not master.features or not member.features:
            return 0.5
        a = np.frombuffer(master.features, dtype=np.float32)
        b = np.frombuffer(member.features, dtype=np.float32)
        if a.size == 0 or b.size == 0:
            return 0.5
        sim = np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-8)
        return float(max(0.0, min(1.0, sim)))


_dedup_service: Optional[DedupService] = None


def get_dedup_service() -> DedupService:
    global _dedup_service
    if _dedup_service is None:
        _dedup_service = DedupService()
    return _dedup_service

__all__ = ['DedupService', 'get_dedup_service']
