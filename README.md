# Local-First AI Agent

An end-to-end, local-first AI Agent that accepts natural language instructions and autonomously drives a web browser to perform tasks like search, click, form-fill, extract content, and return structured results.

## Features

- **Local-only operation**: No external cloud APIs or internet LLM calls
- **Browser automation**: Uses Playwright for reliable web automation
- **Modular architecture**: Clear separation of components
- **Robust error handling**: Retry logic, timeouts, and session memory
- **Multiple interfaces**: CLI and web UI
- **Export capabilities**: JSON and CSV output

## Architecture

```
src/
├── agent/
│   ├── llm_adapter.py      # Local LLM interface
│   ├── parser.py           # Instruction parser
│   ├── planner.py          # Step planner
│   ├── orchestrator.py     # Execution orchestrator
│   ├── browser_controller.py # Playwright wrapper
│   └── extractor.py        # Content extraction
├── utils/
│   └── storage.py          # JSON/CSV export
├── memory/
│   └── session_memory.py   # Task memory
├── prompts/                # LLM prompt templates
├── app.py                  # Flask web interface
└── cli.py                  # Command-line interface
```

## Setup

### Prerequisites

- Python 3.11+
- Node.js (for Playwright)
- Local LLM (GPT4All, Ollama, or LLaMA)

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd local-ai-agent
```

2. Install Python dependencies:
```bash
pip install -r requirements.txt
```

3. Install Playwright browsers:
```bash
playwright install
```

4. Set up local LLM (choose one):
   - **GPT4All**: Download model from https://gpt4all.io/
   - **Ollama**: Install and pull a model: `ollama pull llama2`
   - **LLaMA**: Download weights and use with transformers

### Configuration

Create a `.env` file:
```env
LLM_MODEL_PATH=/path/to/your/model
LLM_TYPE=gpt4all  # or ollama, llama
BROWSER_HEADLESS=true
MEMORY_PERSIST=true
```

## Usage

### CLI Interface

```bash
# Run a search task
python cli.py "search laptops under ₹50,000 and list top 5 with price and link"

# Run with memory persistence
python cli.py --persist-memory "search gaming laptops"

# Run in headful mode (visible browser)
python cli.py --headful "fill contact form on example.com"
```

### Web Interface

1. Start the Flask server:
```bash
python app.py
```

2. Open http://localhost:5000 in your browser

3. Enter your instruction and click "Execute"

### API Endpoints

- `GET /` - Web interface
- `POST /run` - Execute instruction (JSON)
- `GET /results/<task_id>` - Get task results
- `GET /export/<task_id>/csv` - Export results as CSV

## Example Usage

```python
from src.agent.orchestrator import Orchestrator

# Initialize the agent
agent = Orchestrator()

# Execute a task
result = agent.execute("search for best laptops under 50000 rupees")

print(result)
```

## Testing

Run the test suite:
```bash
python -m pytest tests/
```

Run specific tests:
```bash
python -m pytest tests/test_parser.py
python -m pytest tests/test_integration.py
```

## Docker

Build and run with Docker:
```bash
docker build -t local-ai-agent .
docker run -p 5000:5000 local-ai-agent
```

## Troubleshooting

### Common Issues

1. **LLM not responding**: Check model path and ensure it's compatible
2. **Browser automation fails**: Ensure Playwright is installed
3. **Memory issues**: Reduce browser context or use headless mode
4. **Timeout errors**: Increase timeout values in configuration

### Debug Mode

Run with debug logging:
```bash
python cli.py --debug "your instruction here"
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

MIT License - see LICENSE file for details
