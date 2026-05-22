import os
import sys
import json
import base64
import time
import argparse
from pathlib import Path

try:
    import requests
except ImportError:
    print("Error: 'requests' library not found. Install it with: pip install requests")
    sys.exit(1)


class VisionBridge:
    """Bridge between non-vision LLMs and Ollama vision models."""

    def __init__(self, model="minicpm-v:8b", ollama_url="http://localhost:11434"):
        self.model = model
        self.ollama_url = ollama_url

    def _load_image(self, source):
        """Load image and return base64 encoded string."""
        if source.startswith(('http://', 'https://')):
            return self._load_from_url(source)
        elif os.path.isfile(source):
            # Existing file path
            return self._load_from_file(source)
        elif (os.sep in source or '/' in source) and not self._looks_like_base64(source):
            # Looks like a file path (but file doesn't exist)
            return self._load_from_file(source)  # Will raise FileNotFoundError
        else:
            # Assume it's a base64 string
            return self._validate_base64(source)

    def _looks_like_base64(self, s):
        """Check if string looks like base64 encoded data."""
        if len(s) < 4:
            return False
        # Base64 strings are typically long and contain only base64 chars
        import re
        return bool(re.match(r'^[A-Za-z0-9+/=]+$', s)) and len(s) > 100

    def _load_from_file(self, file_path):
        """Load image from local file path."""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Image file not found: {file_path}")

        with open(path, 'rb') as f:
            image_data = f.read()

        return base64.b64encode(image_data).decode('utf-8')

    def _load_from_url(self, url):
        """Download image from URL and encode to base64."""
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        return base64.b64encode(response.content).decode('utf-8')

    def _validate_base64(self, b64_string):
        """Validate and return base64 string."""
        try:
            base64.b64decode(b64_string)
            return b64_string
        except Exception:
            raise ValueError("Invalid base64 string or unsupported image source")

    def _call_ollama(self, image_b64, prompt, timeout=120, retries=3):
        """Call Ollama Vision API with retry logic."""
        payload = {
            "model": self.model,
            "prompt": prompt,
            "images": [image_b64],
            "stream": False
        }

        last_error = None
        for attempt in range(retries):
            try:
                response = requests.post(
                    f"{self.ollama_url}/api/generate",
                    json=payload,
                    timeout=timeout
                )
                response.raise_for_status()
                return response.json()["response"]
            except requests.exceptions.Timeout:
                last_error = f"Ollama API timed out after {timeout}s"
                if attempt < retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
            except requests.exceptions.ConnectionError:
                raise Exception(
                    "Ollama is not running. Start it with: ollama serve"
                )
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 404:
                    raise Exception(
                        f"Model '{self.model}' not found. Install it with: ollama pull {self.model}"
                    )
                raise

        raise Exception(last_error or "Failed after maximum retries")

    def recognize(self, image_source, prompt="请详细描述这张图片的内容", timeout=120, retries=3):
        """Main entry point: recognize image content.

        Returns dict with keys:
            - success (bool): Whether recognition succeeded
            - result (str): Recognition result text
            - model (str): Model used
            - duration (float): Time taken in seconds
            - image_source (str): Original image source
            - error (str): Error message if failed
        """
        start_time = time.time()

        try:
            image_b64 = self._load_image(image_source)
            result = self._call_ollama(image_b64, prompt, timeout=timeout, retries=retries)
            duration = time.time() - start_time

            return {
                "success": True,
                "result": result,
                "model": self.model,
                "duration": round(duration, 2),
                "image_source": image_source
            }
        except Exception as e:
            duration = time.time() - start_time
            return {
                "success": False,
                "error": str(e),
                "model": self.model,
                "duration": round(duration, 2),
                "image_source": image_source
            }


def check_environment(ollama_url="http://localhost:11434"):
    """Check if the environment is ready for image recognition.

    Returns list of error messages. Empty list means all OK.
    """
    errors = []

    # Check Python version
    if sys.version_info < (3, 8):
        errors.append(f"Python 3.8+ required, found {sys.version}")

    # Check requests library
    try:
        import requests
    except ImportError:
        errors.append("Missing 'requests' library. Install with: pip install requests")

    # Check Ollama
    try:
        response = requests.get(f"{ollama_url}/api/tags", timeout=5)
        if response.status_code != 200:
            errors.append(f"Ollama returned status {response.status_code}")
    except requests.exceptions.ConnectionError:
        errors.append(
            "Ollama is not running. Start it with: ollama serve\n"
            "  - Windows: Double-click Ollama icon or run 'ollama serve'\n"
            "  - macOS/Linux: Run 'ollama serve' in terminal"
        )
    except Exception as e:
        errors.append(f"Error connecting to Ollama: {e}")

    return errors


def format_output(result, verbose=False):
    """Format result for terminal output."""
    if result["success"]:
        output = []
        if verbose:
            output.append("[Image Recognition Result]")
            output.append(f"Model: {result['model']}")
            output.append(f"Duration: {result['duration']}s")
            output.append("")
            output.append("---Result---")
        output.append(result["result"])
        return "\n".join(output)
    else:
        return f"Error: {result['error']}"


def main():
    parser = argparse.ArgumentParser(
        description="Recognize image content using local Ollama vision models"
    )
    parser.add_argument(
        "--image", "-i",
        required=True,
        help="Image path, URL, or base64 string"
    )
    parser.add_argument(
        "--prompt", "-p",
        default="请详细描述这张图片的内容",
        help="Prompt for the vision model (default: describe the image)"
    )
    parser.add_argument(
        "--model", "-m",
        default="minicpm-v:8b",
        help="Ollama model to use (default: minicpm-v:8b)"
    )
    parser.add_argument(
        "--ollama-url",
        default="http://localhost:11434",
        help="Ollama API URL (default: http://localhost:11434)"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output in JSON format"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show detailed information"
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=120,
        help="API timeout in seconds (default: 120)"
    )
    parser.add_argument(
        "--retry",
        type=int,
        default=3,
        help="Number of retries on failure (default: 3)"
    )

    args = parser.parse_args()

    bridge = VisionBridge(model=args.model, ollama_url=args.ollama_url)
    result = bridge.recognize(args.image, args.prompt, timeout=args.timeout, retries=args.retry)

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(format_output(result, verbose=args.verbose))

    sys.exit(0 if result["success"] else 1)


if __name__ == "__main__":
    main()
