import base64
import io
from unittest.mock import MagicMock, patch

import pytest
from PIL import Image
from vision import VisionBridge


def image_bytes():
    output = io.BytesIO()
    Image.new('RGB', (8, 8)).save(output, 'PNG')
    return output.getvalue()


@pytest.mark.parametrize('value', ['', '!!!!', 'YWJj\n', base64.b64encode(b'not an image').decode()])
def test_invalid_base64_or_nonimage_rejected(value):
    with pytest.raises(ValueError):
        VisionBridge()._validate_base64(value)


def test_local_and_base64_limits_apply_before_decode(tmp_path):
    bridge = VisionBridge()
    bridge.MAX_IMAGE_BYTES = 10
    file = tmp_path / 'big.png'
    file.write_bytes(image_bytes())
    with pytest.raises(ValueError):
        bridge._load_image(str(file))
    with pytest.raises(ValueError):
        bridge._load_image(base64.b64encode(image_bytes()).decode())


@patch('vision.requests.get')
def test_stream_without_content_length_is_bounded(get):
    bridge = VisionBridge()
    bridge.MAX_IMAGE_BYTES = 10
    response = MagicMock()
    response.headers = {}
    response.iter_content.return_value = [b'a' * 6, b'b' * 6]
    get.return_value.__enter__.return_value = response
    with pytest.raises(ValueError, match='limit'):
        bridge._load_from_url('https://example.invalid/image')
    get.return_value.__exit__.assert_called_once()


@patch('vision.requests.get')
def test_url_image_validated_and_html_rejected(get):
    response = MagicMock()
    response.headers = {}
    get.return_value.__enter__.return_value = response
    data = image_bytes()
    response.iter_content.return_value = [data]
    assert base64.b64decode(VisionBridge()._load_from_url('https://example.invalid/image')) == data
    response.iter_content.return_value = [b'<html>not an image</html>']
    with pytest.raises(ValueError):
        VisionBridge()._load_from_url('https://example.invalid/image')


def test_pixel_limit_rejects_image():
    bridge = VisionBridge()
    bridge.MAX_IMAGE_PIXELS = 1
    with pytest.raises(ValueError, match='pixel limit'):
        bridge._encode_image(image_bytes())
