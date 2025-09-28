# 🚀 Local AI Agent - Setup Guide

## Quick Start

### 1. **Install Dependencies**
```bash
pip install -r requirements.txt
playwright install
```

### 2. **Configure LLM (Choose One)**

#### Option A: Ollama (Recommended)
```bash
# Install Ollama from https://ollama.ai/
# Then pull a model:
ollama pull llama2
ollama pull mistral
```

#### Option B: GPT4All
```bash
# Download model from https://gpt4all.io/
# Set model path in environment
export LLM_MODEL_PATH=/path/to/your/model
```

#### Option C: LLaMA with Transformers
```bash
pip install transformers torch
# Download model weights
```

### 3. **Set Environment Variables**
```bash
# For Ollama (recommended)
export LLM_TYPE=ollama
export LLM_MODEL_NAME=llama2

# For GPT4All
export LLM_TYPE=gpt4all
export LLM_MODEL_PATH=/path/to/model

# For LLaMA
export LLM_TYPE=llama
export LLM_MODEL_PATH=/path/to/model
```

### 4. **Run the Agent**

#### Command Line Interface:
```bash
# Basic usage
python cli.py "search laptops under ₹50,000 and list top 5 with price and link"

# With visible browser
python cli.py "navigate to https://example.com and take a screenshot" --headful

# Save results to file
python cli.py "search gaming laptops" --output results.json --format json

# Show help
python cli.py --help
```

#### Web Interface:
```bash
# Start web server
python app.py

# Open browser to http://localhost:5000
```

#### Programmatic Usage:
```python
import asyncio
from src.agent.orchestrator import OrchestratorFactory

async def main():
    orchestrator = OrchestratorFactory.create_orchestrator()
    result = await orchestrator.execute("your instruction here")
    print(result.results)

asyncio.run(main())
```

## 🔧 Configuration Options

### Environment Variables:
- `LLM_TYPE`: ollama, gpt4all, llama
- `LLM_MODEL_PATH`: Path to model file
- `LLM_MODEL_NAME`: Model name for Ollama
- `BROWSER_HEADLESS`: true/false
- `BROWSER_TYPE`: chromium, firefox, webkit
- `MEMORY_PERSIST`: true/false
- `OUTPUT_DIR`: Directory for exports

### Browser Options:
- `--headful`: Run browser in visible mode
- `--browser`: Choose browser type
- `--persist-memory`: Save session memory

## 📝 Example Commands

### Search Tasks:
```bash
python cli.py "search laptops under ₹50,000 and list top 5 with price and link"
python cli.py "search for best gaming laptops with high ratings"
python cli.py "find cheap smartphones under ₹20,000"
```

### Navigation Tasks:
```bash
python cli.py "navigate to https://example.com and take a screenshot"
python cli.py "go to https://github.com and extract repository information"
```

### Extraction Tasks:
```bash
python cli.py "extract all product information from the current page"
python cli.py "get all links from https://example.com"
```

### Form Tasks:
```bash
python cli.py "fill the contact form on https://example.com with name 'John Doe' and email 'john@example.com'"
```

## 🧪 Testing

### Run Tests:
```bash
python -m pytest tests/
python -m pytest tests/test_parser.py
python -m pytest tests/test_integration.py
```

### Test Simple Functionality:
```bash
python test_simple.py
```

### Run Demo:
```bash
python demo_search.py
```

## 🐳 Docker Usage

### Build and Run:
```bash
docker build -t local-ai-agent .
docker run -p 5000:5000 local-ai-agent
```

## 🔍 Troubleshooting

### Common Issues:

1. **LLM not responding:**
   - Check if Ollama is running: `ollama list`
   - Verify model is installed: `ollama pull llama2`
   - Check environment variables

2. **Browser automation fails:**
   - Install Playwright browsers: `playwright install`
   - Check if browser is available
   - Try different browser type

3. **Import errors:**
   - Make sure you're in the project directory
   - Check Python path includes `src/`
   - Install missing dependencies

4. **Memory issues:**
   - Use headless mode: `BROWSER_HEADLESS=true`
   - Reduce browser context
   - Clear session memory: `python cli.py --clear-memory`

### Debug Mode:
```bash
python cli.py --debug "your instruction here"
```

## 📊 Monitoring

### Check Status:
```bash
python cli.py --stats
python cli.py --history
```

### Export Data:
```bash
python cli.py --export-memory memory_backup.json
```

## 🎯 Advanced Usage

### Custom LLM Configuration:
```python
from src.agent.llm_adapter import LLMAdapterFactory
from src.agent.orchestrator import OrchestratorFactory

# Create custom LLM adapter
llm_adapter = LLMAdapterFactory.create_adapter('ollama', model_name='mistral')
orchestrator = OrchestratorFactory.create_orchestrator(llm_manager=llm_adapter)
```

### Custom Browser Configuration:
```python
from src.agent.browser_controller import BrowserConfig

browser_config = BrowserConfig(
    headless=False,
    browser_type="firefox",
    viewport_width=1920,
    viewport_height=1080
)
```

### Custom Storage Configuration:
```python
from src.utils.storage import ExportConfig

storage_config = ExportConfig(
    output_dir="custom_exports",
    json_format=True,
    csv_format=True,
    include_metadata=True
)
```

## 🚀 Production Deployment

### Environment Setup:
```bash
# Set production environment
export FLASK_ENV=production
export DEBUG=false
export BROWSER_HEADLESS=true
export MEMORY_PERSIST=true
```

### Run with Gunicorn:
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### Docker Production:
```bash
docker run -d -p 5000:5000 --name ai-agent local-ai-agent
```

## 📚 API Documentation

### Web API Endpoints:
- `GET /` - Web interface
- `POST /run` - Execute task
- `GET /results/<task_id>` - Get task results
- `GET /export/<task_id>/csv` - Export as CSV
- `GET /export/<task_id>/json` - Export as JSON
- `GET /history` - Get task history
- `GET /stats` - Get session stats

### Example API Usage:
```bash
curl -X POST http://localhost:5000/run \
  -H "Content-Type: application/json" \
  -d '{"instruction": "search laptops under ₹50,000"}'
```

## 🎉 You're Ready!

The Local AI Agent is now set up and ready to use. Start with simple commands and gradually explore more complex tasks. The system is designed to be robust and handle various web automation scenarios.

For more examples and advanced usage, check the `demo_search.py` file and the test suite in the `tests/` directory.
