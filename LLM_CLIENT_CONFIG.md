# LLM Client Configuration Guide

This guide explains how to configure and test the LLM client with your staging environment.

## Overview

The LLM client (`tests/llm_client.py`) is a generic client that supports OpenAI-compatible APIs, including:
- OpenAI API
- Azure OpenAI
- Anthropic Claude API
- Other OpenAI-compatible providers

## Configuration

### 1. Environment Variables

The LLM client uses the following environment variables:

#### Required:
- **`LLM_API_BASE_URL`**: Your staging LLM API endpoint URL
  - Example: `https://api.staging.example.com/v1`
  - Example (OpenAI): `https://api.openai.com/v1`
  - Example (Azure): `https://your-resource.openai.azure.com`

- **`LLM_API_KEY`**: Your authentication token for the staging environment
  - This should be kept secure and never committed to git
  - Set via environment variable in container definition

#### Optional:
- **`LLM_MODEL`**: Model name to use (defaults to provider default if not set)
  - Example: `gpt-4`, `gpt-3.5-turbo`, `claude-3-opus`, etc.

### 2. HTTP Client Configuration

Add these variables to your environment files:

#### `http-client.env.json` (public, can be committed):
```json
{
  "dev": {
    "llmStagingBaseUrl": "https://api.staging.example.com/v1",
    "llmModel": "gpt-4"
  },
  "local": {
    "llmStagingBaseUrl": "https://api.staging.example.com/v1",
    "llmModel": "gpt-4"
  }
}
```

#### `http-client.private.env.json` (private, git-ignored):
```json
{
  "dev": {
    "llmStagingApiKey": "your-staging-api-token-here"
  },
  "local": {
    "llmStagingApiKey": "your-staging-api-token-here"
  }
}
```

## Usage

### Command Line

```bash
# Health check
python tests/llm_client.py --test health

# Simple completion
python tests/llm_client.py --test simple --prompt "Hello, how are you?"

# Chat completion
python tests/llm_client.py --test chat --prompt "What is Python?"

# Custom model
python tests/llm_client.py --test simple --prompt "Hello" --model "gpt-3.5-turbo"
```

### Programmatic Usage

```python
from llm_client import LLMClient

# Initialize client (reads from environment variables)
client = LLMClient()

# Simple completion
result = client.simple_completion("What is AI?")
print(result["content"])

# Chat completion with context
messages = [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "What is Python?"}
]
result = client.chat_completion(messages)
print(result["content"])

# Health check
health = client.health_check()
print(health["status"])
```

## Testing

### Run Full Test Suite

```bash
python tests/test_llm_client.py
```

This runs:
1. Health check test
2. Simple completion test
3. Chat completion test
4. Performance benchmark

### HTTP Test File

Use the HTTP test file: `llm-client-tests.http`

This file contains ready-to-run tests that:
- Create environments with LLM configuration
- Run health checks
- Test completion functionality
- Verify API key masking

## API Compatibility

The client auto-detects API type from the URL, but you can also manually specify:

### OpenAI-Compatible APIs
- Uses `/v1/chat/completions` endpoint
- Bearer token authentication
- Standard message format

### Anthropic Claude API
- Uses `/v1/messages` endpoint
- `x-api-key` header authentication
- Slightly different message format

## Security

### API Key Handling

1. **Never commit API keys** to git
2. **Use environment variables** in container definitions
3. **API keys are masked** in environment definition responses
4. **Check masking** using the HTTP test file

### Token Storage

For Orca Facade:
- API keys are passed via `env` array in environment definition
- Keys are automatically masked in API responses
- Keys are accessible in the container via environment variables

## Troubleshooting

### Connection Errors

```bash
# Check if URL is accessible
curl -H "Authorization: Bearer YOUR_TOKEN" https://api.staging.example.com/v1/models

# Check environment variables
python -c "import os; print('URL:', os.environ.get('LLM_API_BASE_URL')); print('Key:', 'SET' if os.environ.get('LLM_API_KEY') else 'NOT SET')"
```

### Authentication Errors

- Verify API key is correct
- Check if key has proper permissions
- Ensure key is valid for staging environment

### Model Errors

- Verify model name is correct for your provider
- Check if model is available in staging
- Use provider's model list endpoint to verify

## Example: OpenAI Staging

```json
{
  "env": [
    {
      "key": "LLM_API_BASE_URL",
      "value": "https://api.openai.com/v1"
    },
    {
      "key": "LLM_API_KEY",
      "value": "sk-staging-..."
    },
    {
      "key": "LLM_MODEL",
      "value": "gpt-4"
    }
  ]
}
```

## Example: Azure OpenAI Staging

```json
{
  "env": [
    {
      "key": "LLM_API_BASE_URL",
      "value": "https://your-resource.openai.azure.com"
    },
    {
      "key": "LLM_API_KEY",
      "value": "your-azure-api-key"
    },
    {
      "key": "LLM_MODEL",
      "value": "gpt-4"
    }
  ]
}
```

## Example: Anthropic Claude Staging

```json
{
  "env": [
    {
      "key": "LLM_API_BASE_URL",
      "value": "https://api.anthropic.com/v1"
    },
    {
      "key": "LLM_API_KEY",
      "value": "sk-ant-staging-..."
    },
    {
      "key": "LLM_MODEL",
      "value": "claude-3-opus-20240229"
    }
  ]
}
```

## Next Steps

1. **Update environment files** with your staging URL and model
2. **Add API key** to `http-client.private.env.json`
3. **Run HTTP tests** using `llm-client-tests.http`
4. **Review logs** to verify functionality
5. **Adjust tests** as needed for your specific LLM provider

