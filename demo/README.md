# Jarvus Demo

## Configuration

### GPT Model Selection

The system supports both GPT-4o and GPT-5-nano models. You can choose which one to use by setting environment variables:

#### Environment Variables

Create a `.env` file in the `demo/` directory with the following variables:

```bash
# Choose between 'gpt-4o' (faster, cheaper) or 'gpt-5-nano' (more powerful, slower)
GPT_MODEL=gpt-4o

# OpenAI API Key
OPENAI_API_KEY=your_openai_api_key_here
```

#### Model Comparison

- **GPT-4o** (default):
  - Faster response times
  - Lower cost
  - Good for most use cases
  - Uses standard OpenAI Chat Completions API

- **GPT-5-nano**:
  - More powerful reasoning
  - Slower response times
  - Higher cost
  - Uses OpenAI Responses API with web search capabilities

#### API Key Configuration

You can use either:
- `OPENAI_API_KEY` (recommended)
- `GPT5_API_KEY` (legacy support)

Both should contain your OpenAI API key.

## Running the Demo

1. Set up your environment variables
2. Install dependencies: `pip install -r requirements.txt`
3. Run the application: `python app.py`
4. Open your browser to `http://localhost:5000`

## Features

- Real-time GPT search integration
- Comprehensive logging of API requests and responses
- Support for both GPT-4o and GPT-5-nano models
- Streaming search results in the UI
- Enhanced insurance analysis with Medicare document parsing