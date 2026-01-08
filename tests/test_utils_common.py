"""
Unit tests for app.utils.common.
"""
import hashlib
import io

import numpy as np
import pytest
from PIL import Image

pytest.importorskip("pillow_heif")
pytest.importorskip("imagehash")

from app.utils import common as common_utils


def test_get_hash_bytesio_resets_pointer():
    data = b"hello"
    bio = io.BytesIO(data)
    result = common_utils.get_hash(bio)
    assert result == hashlib.sha1(data).hexdigest()
    assert bio.tell() == 0


def test_get_hash_bytes():
    data = b"hello"
    result = common_utils.get_hash(data)
    assert result == hashlib.sha1(data).hexdigest()


def test_get_string_hash():
    value = "abc"
    result = common_utils.get_string_hash(value)
    assert result == hashlib.sha1(value.encode("utf8")).hexdigest()


def test_get_file_hash(tmp_path):
    path = tmp_path / "data.bin"
    payload = b"sample"
    path.write_bytes(payload)
    result = common_utils.get_file_hash(str(path))
    assert result == hashlib.sha1(payload).hexdigest()


def test_softmax_normalized():
    scores = np.array([1.0, 2.0, 3.0])
    result = common_utils.softmax(scores)
    assert result.shape == scores.shape
    assert pytest.approx(result.sum(), rel=1e-6) == 1.0
    assert (result > 0).all()


def test_format_seconds():
    assert common_utils.format_seconds(3661) == "01:01:01"


def test_create_checkerboard_colors():
    img = common_utils.create_checkerboard(
        (32, 32),
        block_size=16,
        color1=(10, 10, 10),
        color2=(20, 20, 20),
    )
    assert img.size == (32, 32)
    assert img.getpixel((0, 0)) == (20, 20, 20)
    assert img.getpixel((17, 0)) == (10, 10, 10)


def test_resize_image_with_aspect_ratio(tmp_path):
    img = Image.new("RGB", (100, 50), color=(123, 0, 0))
    path = tmp_path / "sample.jpg"
    img.save(path)
    resized = common_utils.resize_image_with_aspect_ratio(
        str(path),
        (50, 50),
        convert_rgb=True,
    )
    assert resized.size == (50, 25)
