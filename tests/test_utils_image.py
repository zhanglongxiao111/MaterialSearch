"""
Unit tests for app.utils.image.
"""
import pytest
from PIL import Image

pytest.importorskip("imagehash")

from app.utils import image as image_utils


def test_get_standard_aspect_ratio():
    assert image_utils.get_standard_aspect_ratio(1.778) == "16:9"
    assert image_utils.get_standard_aspect_ratio(2.1) == "2.10:1"


def test_calculate_image_properties(tmp_path):
    img = Image.new("RGB", (120, 60), color=(10, 20, 30))
    path = tmp_path / "sample.png"
    img.save(path)
    props = image_utils.calculate_image_properties(str(path))
    assert props is not None
    assert props["width"] == 120
    assert props["height"] == 60
    assert props["aspect_ratio"] == 2.0
    assert props["aspect_ratio_standard"] == "2:1"
    assert props["file_size"] > 0
    assert props["file_format"] in ("png", "jpg", "jpeg")
    assert "phash" in props


def test_calculate_image_properties_missing(tmp_path):
    missing = tmp_path / "missing.png"
    assert image_utils.calculate_image_properties(str(missing)) is None
