---
name: vision-bridge
description: "Recognize image content using local Ollama vision models. Use when the user asks to describe an image, analyze a screenshot, read text from a picture, or understand chart/graph content. Supports local files, URLs, and base64 input."
allowed-tools: Bash, Read
---

# Vision Bridge - Image Recognition

This skill enables any LLM to recognize image content by using local Ollama vision models as a bridge.

## When to Use

Trigger this skill when:
- User asks to "describe this image", "what's in this picture", "识别这张图片"
- User provides a screenshot and asks what it shows
- User asks to analyze a chart, graph, or diagram
- User asks to extract text from an image
- User shares an image file path or URL and wants it understood

## Prerequisites Check

Before using, verify the environment:

```bash
# Check if Ollama is running
curl -s http://localhost:11434/api/tags > /dev/null 2>&1 && echo "Ollama: OK" || echo "Ollama: NOT RUNNING - Start with: ollama serve"

# Check available vision models
curl -s http://localhost:11434/api/tags | python3 -c "import sys,json; models=[m['name'] for m in json.load(sys.stdin)['models']]; print('Vision models:', ', '.join(models) if models else 'None found - Install with: ollama pull minicpm-v:8b')"
```

## Usage

### Basic Usage

```bash
# Get the skill's script directory
SKILL_DIR="$(dirname "$(readlink -f "$0")")/scripts"  # Adjust path as needed

# Recognize a local image
python3 "$SKILL_DIR/vision.py" --image /path/to/image.png

# Recognize from URL
python3 "$SKILL_DIR/vision.py" --image https://example.com/photo.jpg

# Custom prompt for specific tasks
python3 "$SKILL_DIR/vision.py" --image /path/to/screenshot.png --prompt "Extract all code from this screenshot"
python3 "$SKILL_DIR/vision.py" --image /path/to/chart.png --prompt "Describe the data trends in this chart"
python3 "$SKILL_DIR/vision.py" --image /path/to/document.png --prompt "Read and transcribe all text"
```

### Advanced Options

```bash
# Use a specific model
python3 "$SKILL_DIR/vision.py" --image photo.png --model llava:13b

# JSON output for programmatic use
python3 "$SKILL_DIR/vision.py" --image photo.png --json

# Verbose output with timing info
python3 "$SKILL_DIR/vision.py" --image photo.png --verbose

# Custom Ollama URL (if running remotely)
python3 "$SKILL_DIR/vision.py" --image photo.png --ollama-url http://192.168.1.100:11434
```

## Recommended Models

| Model | Size | Best For |
|-------|------|----------|
| `minicpm-v:8b` | 5.5GB | Chinese text, general use (recommended) |
| `llava:7b` | 4.7GB | English text, detailed descriptions |
| `moondream:latest` | 1.7GB | Low-spec machines, quick recognition |
| `llava:13b` | 8GB | Highest accuracy, needs more RAM |

Install a model: `ollama pull minicpm-v:8b`

## Error Handling

If you encounter errors:

1. **"Ollama is not running"**: Start Ollama with `ollama serve`
2. **"Model not found"**: Install with `ollama pull <model-name>`
3. **"File not found"**: Check the image path is correct and file exists
4. **"Timeout"**: Try a smaller image or use a lighter model like `moondream`

## Integration Examples

When a user says:
- "What's in this image?" → Run vision.py with the image
- "Can you read this screenshot?" → Use prompt "Extract all text from this screenshot"
- "Analyze this chart" → Use prompt "Describe the data, trends, and key insights in this chart"
- "这个图片是什么？" → Run vision.py with Chinese prompt "请详细描述这张图片的内容"
