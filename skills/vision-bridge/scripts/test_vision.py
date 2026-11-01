import pytest
import sys
import os
import subprocess
import requests
from unittest.mock import patch, MagicMock

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(__file__))

from vision import VisionBridge


class TestVisionBridgeInit:
    def test_default_init(self):
        bridge = VisionBridge()
        assert bridge.model == "minicpm-v:8b"
        assert bridge.ollama_url == "http://localhost:11434"

    def test_custom_init(self):
        bridge = VisionBridge(model="llava:7b", ollama_url="http://localhost:9999")
        assert bridge.model == "llava:7b"
        assert bridge.ollama_url == "http://localhost:9999"


import base64
import io
from PIL import Image


def png_bytes():
    output = io.BytesIO()
    Image.new('RGB', (2, 2), 'red').save(output, format='PNG')
    return output.getvalue()


class TestImageLoading:
    def setup_method(self):
        self.bridge = VisionBridge()

    def test_load_from_file(self, tmp_path):
        """Test loading image from local file."""
        # Create a minimal PNG file (1x1 pixel)
        png_data = png_bytes()
        img_path = tmp_path / "test.png"
        img_path.write_bytes(png_data)

        result = self.bridge._load_image(str(img_path))
        assert result is not None
        assert len(result) > 0
        # Verify it's valid base64
        base64.b64decode(result)

    @patch('vision.requests.get')
    def test_load_from_url(self, mock_get):
        """Test loading image from URL."""
        url = "https://httpbin.org/image/png"
        response = MagicMock()
        response.headers = {}
        data = png_bytes()
        response.iter_content.return_value = [data]
        mock_get.return_value.__enter__.return_value = response
        result = self.bridge._load_image(url)
        assert base64.b64decode(result) == data

    def test_load_base64_string(self):
        """Test passing base64 string directly."""
        b64 = base64.b64encode(png_bytes()).decode()
        result = self.bridge._load_image(b64)
        assert result == b64

    def test_load_nonexistent_file(self):
        """Test error on nonexistent file."""
        with pytest.raises(FileNotFoundError):
            self.bridge._load_image("/nonexistent/image.png")


class TestOllamaAPI:
    def setup_method(self):
        self.bridge = VisionBridge()

    @patch('vision.requests.post')
    def test_call_ollama_success(self, mock_post):
        """Test successful Ollama API call."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"response": "A cat sitting on a couch"}
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        result = self.bridge._call_ollama("base64data", "describe this")

        assert result == "A cat sitting on a couch"
        mock_post.assert_called_once()

        # Verify the payload
        call_args = mock_post.call_args
        payload = call_args[1]['json']
        assert payload['model'] == "minicpm-v:8b"
        assert payload['prompt'] == "describe this"
        assert payload['images'] == ["base64data"]
        assert payload['stream'] is False

    @patch('vision.requests.post')
    def test_call_ollama_timeout(self, mock_post):
        """Test Ollama API timeout handling."""
        mock_post.side_effect = requests.exceptions.Timeout()

        with pytest.raises(Exception) as exc_info:
            self.bridge._call_ollama("base64data", "describe")

        assert "timed out" in str(exc_info.value).lower() or "timeout" in str(exc_info.value).lower()

    @patch('vision.requests.post')
    def test_call_ollama_connection_error(self, mock_post):
        """Test Ollama connection error handling."""
        mock_post.side_effect = requests.exceptions.ConnectionError()

        with pytest.raises(Exception) as exc_info:
            self.bridge._call_ollama("base64data", "describe")

        assert "not running" in str(exc_info.value).lower() or "connection" in str(exc_info.value).lower()


class TestRecognize:
    def setup_method(self):
        self.bridge = VisionBridge()

    @patch.object(VisionBridge, '_load_image')
    @patch.object(VisionBridge, '_call_ollama')
    def test_recognize_success(self, mock_call, mock_load, tmp_path):
        """Test successful image recognition."""
        mock_load.return_value = "base64data"
        mock_call.return_value = "This is a test image"

        result = self.bridge.recognize("test.png")

        assert result["success"] is True
        assert result["result"] == "This is a test image"
        assert result["model"] == "minicpm-v:8b"
        assert "duration" in result

    @patch.object(VisionBridge, '_load_image')
    def test_recognize_image_load_error(self, mock_load):
        """Test error handling when image loading fails."""
        mock_load.side_effect = FileNotFoundError("File not found")

        result = self.bridge.recognize("nonexistent.png")

        assert result["success"] is False
        assert "error" in result

    @patch.object(VisionBridge, '_load_image')
    @patch.object(VisionBridge, '_call_ollama')
    def test_recognize_custom_prompt(self, mock_call, mock_load):
        """Test recognize with custom prompt."""
        mock_load.return_value = "base64data"
        mock_call.return_value = "Text extracted"

        result = self.bridge.recognize("test.png", prompt="Extract all text")

        assert result["success"] is True
        mock_call.assert_called_once_with("base64data", "Extract all text", timeout=120, retries=3)


class TestCLI:
    def test_help_output(self):
        """Test CLI help displays correctly."""
        result = subprocess.run(
            [sys.executable, "vision.py", "--help"],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(__file__)
        )
        assert result.returncode == 0
        assert "--image" in result.stdout
        assert "--prompt" in result.stdout
        assert "--model" in result.stdout

    def test_missing_image_arg(self):
        """Test error when --image is missing."""
        result = subprocess.run(
            [sys.executable, "vision.py"],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(__file__)
        )
        assert result.returncode != 0
        assert "required" in result.stderr.lower() or "image" in result.stderr.lower()


class TestEnvironmentCheck:
    @patch('vision.requests.get')
    def test_check_ollama_running(self, mock_get):
        """Test detection of running Ollama."""
        mock_get.return_value = MagicMock(status_code=200)

        from vision import check_environment
        errors = check_environment()

        # Should not have Ollama error
        ollama_errors = [e for e in errors if "ollama" in e.lower()]
        assert len(ollama_errors) == 0

    @patch('vision.requests.get')
    def test_check_ollama_not_running(self, mock_get):
        """Test detection of Ollama not running."""
        mock_get.side_effect = requests.exceptions.ConnectionError()

        from vision import check_environment
        errors = check_environment()

        ollama_errors = [e for e in errors if "ollama" in e.lower()]
        assert len(ollama_errors) > 0
