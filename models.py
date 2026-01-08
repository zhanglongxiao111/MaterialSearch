import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from config import SQLALCHEMY_DATABASE_URL
from app.models import (
    BaseModel,
    BaseModelProject,
    BaseModelPexelsVideo,
    Image,
    Video,
    PDFPage,
    ProjectImage,
    ProjectVideo,
    ProjectPDFPage,
    Project,
    DedupJob,
    DedupResult,
    PexelsVideo,
)

folder_path = os.path.dirname(SQLALCHEMY_DATABASE_URL.replace("sqlite:///", ""))
if folder_path and not os.path.exists(folder_path):
    os.makedirs(folder_path)

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}
)
DatabaseSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)

engine_pexels_video = create_engine(
    "sqlite:///./PexelsVideo.db",
    connect_args={"check_same_thread": False}
)
DatabaseSessionPexelsVideo = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine_pexels_video
)


def create_tables():
    BaseModel.metadata.create_all(bind=engine)
    BaseModelPexelsVideo.metadata.create_all(bind=engine_pexels_video)


__all__ = [
    "BaseModel",
    "BaseModelProject",
    "BaseModelPexelsVideo",
    "Image",
    "Video",
    "PDFPage",
    "ProjectImage",
    "ProjectVideo",
    "ProjectPDFPage",
    "Project",
    "DedupJob",
    "DedupResult",
    "PexelsVideo",
    "DatabaseSession",
    "DatabaseSessionPexelsVideo",
    "create_tables",
]