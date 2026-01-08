from sqlalchemy.ext.declarative import declarative_base

BaseModel = declarative_base()
BaseModelProject = declarative_base()
BaseModelPexelsVideo = declarative_base()

__all__ = [
    "BaseModel",
    "BaseModelProject",
    "BaseModelPexelsVideo",
]