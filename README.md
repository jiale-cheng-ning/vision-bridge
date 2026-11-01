# Vision Bridge

A Claude Code plugin that enables any LLM to recognize image content through local Ollama vision models.

## Features

- **Zero cost**: Uses local models, no paid APIs needed
- **Privacy safe**: Image data never leaves your machine
- **Universal compatibility**: Works with any LLM through Claude Code
- **Multiple input types**: Local files, URLs, and base64 strings
- **Custom prompts**: Tailor recognition for specific tasks
- **Error recovery**: Automatic retries with exponential backoff

## Quick Start

### 1. Install Ollama

Download from [ollama.ai](https://ollama.ai) and install.

### 2. Pull a Vision Model

```bash
# Recommended for Chinese + English
ollama pull minicpm-v:8b

# Or lighter alternatives
ollama pull llava:7b        # Good English support
ollama pull moondream       # Ultra lightweight (1.7GB)
```

### 3. Install the Plugin

```bash
# Clone to Claude Code plugins directory
git clone https://github.com/jiale-cheng-ning/vision-bridge ~/.claude/plugins/vision-bridge
python -m pip install -r ~/.claude/plugins/vision-bridge/skills/vision-bridge/scripts/requirements.txt
```

### 4. Use It!

In Claude Code, just ask about any image:

```
"What's in this image? /path/to/photo.png"
"识别这张截图"
"Analyze this chart: https://example.com/chart.png"
```

## Usage Examples

### Describe an Image
```
User: What does this image show? ~/Desktop/screenshot.png
Claude: [Runs vision-bridge] The image shows...
```

### Extract Text from Screenshot
```
User: Can you read the error message in this screenshot? ~/errors.png
Claude: [Runs vision-bridge with text extraction prompt] The error message says...
```

### Analyze Data Visualization
```
User: What trends do you see in this chart? ~/sales_chart.png
Claude: [Runs vision-bridge with analysis prompt] The chart shows...
```

## CLI Reference

Images are validated before inference: PNG, JPEG, WEBP, GIF and BMP, up to
10 MiB and 40 million pixels. Invalid Base64 and damaged images are rejected.
URL downloads are streamed with the same byte limit, including responses that
omit Content-Length. For animated images, decoding checks the first frame.

```bash
python3 vision.py [options]

Required:
  --image, -i      Image path, URL, or base64 string

Options:
  --prompt, -p     Custom prompt (default: describe the image)
  --model, -m      Ollama model (default: minicpm-v:8b)
  --ollama-url     Ollama API URL (default: http://localhost:11434)
  --json           Output as JSON
  --verbose, -v    Show detailed info
  --timeout        API timeout in seconds (default: 120)
  --retry          Retry count (default: 3)
```

## Recommended Models

| Model | Size | Speed | Accuracy | Best For |
|-------|------|-------|----------|----------|
| `minicpm-v:8b` | 5.5GB | Fast | High | Chinese + English, general use |
| `llava:7b` | 4.7GB | Fast | Good | English descriptions |
| `moondream` | 1.7GB | Very Fast | Basic | Low-spec machines |
| `llava:13b` | 8GB | Medium | Highest | Maximum accuracy |

## Troubleshooting

### Ollama not running
```
Error: Ollama is not running
Solution: Start Ollama with `ollama serve`
```

### Model not found
```
Error: Model 'minicpm-v:8b' not found
Solution: Install with `ollama pull minicpm-v:8b`
```

### Image loading failed
```
Error: Image file not found
Solution: Check the file path and ensure the file exists
```

### Timeout
```
Error: Ollama API timed out
Solution: Try a smaller image or use a lighter model
```

## Development

### Running Tests

```bash
cd skills/vision-bridge/scripts
pip install pytest requests
python -m pytest test_vision.py -v
```

### Project Structure

```
vision-bridge/
├── .claude-plugin/
│   └── plugin.json              # Plugin metadata
├── skills/
│   └── vision-bridge/
│       ├── SKILL.md             # Skill instructions
│       ├── scripts/
│       │   ├── vision.py        # Core script
│       │   ├── test_vision.py   # Tests
│       │   └── requirements.txt # Dependencies
│       └── models.json          # Model config
├── README.md
├── LICENSE
└── CHANGELOG.md
```

## License

MIT License - see [LICENSE](LICENSE)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests: `python -m pytest skills/vision-bridge/scripts/ -v`
5. Submit a pull request
