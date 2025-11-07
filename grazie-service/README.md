# Grazie Client Libraries

This repository contains comprehensive client libraries for the Grazie AI API, available in both Python and JavaScript.

## Overview

The Grazie clients provide easy-to-use interfaces for interacting with JetBrains' Grazie AI platform, supporting features like:

- **Multiple AI Models**: GPT-4o, Claude Sonnet, and other state-of-the-art models
- **Streaming Support**: Real-time response streaming with proper chunk handling
- **Parameter Configuration**: Temperature, top-p, top-k, and other model parameters
- **Metadata Extraction**: Token usage, response timing, and model information
- **JWT Authentication**: Secure token-based authentication
- **Environment Support**: Both staging and production environments

## Python Client

### Installation

```bash
pip install -r requirements.txt
```

### Usage

```python
from grazie_client import GrazieClient

# Initialize client
client = GrazieClient(environment="staging")

# Simple chat
response = client.simple_chat(
    user_message="Hello, how are you?",
    system_message="You are a helpful assistant."
)
print(response)

# Streaming chat
messages = [
    {"type": "system", "content": "You are a helpful assistant."},
    {"type": "user", "content": "Tell me a joke."}
]

for chunk in client.chat_stream(messages):
    if chunk.get("type") == "Content":
        print(chunk.get("content", ""), end="", flush=True)
```

### Python SDK Client

For enhanced functionality, use the SDK-based client:

```python
from grazie_sdk_client import GrazieSDKClient

# Initialize SDK client
client = GrazieSDKClient(environment="staging")

# Use Claude Sonnet 4 (default)
response = client.sonnet4_chat(
    user_message="Explain quantum computing",
    system_message="You are a physics teacher."
)
print(response)
```

## JavaScript Client

### Installation

```bash
npm install
```

### Usage

```javascript
const GrazieClient = require('./grazie_client.js');

async function main() {
    // Initialize client
    const client = new GrazieClient(null, "staging");
    
    // Simple chat
    const response = await client.simpleChat(
        "Hello, how are you?",
        "You are a helpful assistant."
    );
    console.log(response);
    
    // Streaming chat
    const messages = [
        { type: "system", content: "You are a helpful assistant." },
        { type: "user", content: "Tell me a joke." }
    ];
    
    for await (const chunk of client.chatStream(messages)) {
        if (chunk.type === "Content") {
            process.stdout.write(chunk.content || "");
        }
    }
}

main().catch(console.error);
```

### TypeScript Support

The JavaScript client includes TypeScript definitions:

```typescript
import GrazieClient, { GrazieMessage, GrazieParameters } from './grazie_client';

const client = new GrazieClient(null, "staging");

const messages: GrazieMessage[] = [
    { type: "system", content: "You are a helpful assistant." },
    { type: "user", content: "Hello!" }
];

const parameters: GrazieParameters = {
    temperature: 0.7,
    top_p: 0.9
};

const response = await client.chatComplete(messages, "openai-gpt-4o", parameters);
```

## Configuration

### Environment Variables

Set one of the following environment variables with your JWT token:

```bash
export GRAZIE_JWT_TOKEN="your-jwt-token-here"
# or
export USER_JWT_TOKEN="your-jwt-token-here"
```

### Available Models

Both clients support various AI models:

- `openai-gpt-4o` - GPT-4o
- `anthropic-claude-3-5-sonnet-20241022` - Claude Sonnet 4
- And many others (check with `getAvailableModels()`)

## Features

### Parameter Configuration

Both clients support comprehensive parameter configuration:

```python
# Python
creative_params = client.create_creative_params("high")
deterministic_params = client.create_deterministic_params(seed=42)
focused_params = client.create_focused_params("medium")
json_params = client.create_json_response_params()
```

```javascript
// JavaScript
const creativeParams = client.createCreativeParams("high");
const deterministicParams = client.createDeterministicParams(42);
const focusedParams = client.createFocusedParams("medium");
const jsonParams = client.createJsonResponseParams();
```

### Streaming with Metadata

Get response content along with metadata:

```python
# Python
content, metadata = client.chat_stream_with_metadata(messages)
print(f"Content: {content}")
print(f"Tokens used: {metadata['tokens_spent']}")
```

```javascript
// JavaScript
const [content, metadata] = await client.chatStreamWithMetadata(messages);
console.log(`Content: ${content}`);
console.log(`Tokens used: ${metadata.tokens_spent}`);
```

## Examples

### Python Examples

- `example_usage.py` - Basic usage with the HTTP client
- `example_usage_sdk.py` - Advanced usage with the SDK client
- `get_models.py` - Model discovery and capabilities

### JavaScript Examples

- `example_usage.js` - Comprehensive JavaScript usage examples

Run examples:

```bash
# Python
python example_usage.py
python example_usage_sdk.py

# JavaScript
node example_usage.js
npm run demo
```

## API Reference

### Python Client Methods

- `simple_chat(user_message, system_message=None, profile="openai-gpt-4o", parameters=None)`
- `chat_stream(messages, profile="openai-gpt-4o", parameters=None)`
- `chat_complete(messages, profile="openai-gpt-4o", parameters=None)`
- `get_available_models()`
- `get_model_capabilities(profile)`
- `create_creative_params(level="medium")`
- `create_deterministic_params(seed=42)`
- `create_focused_params(level="medium")`
- `create_json_response_params()`

### JavaScript Client Methods

- `simpleChat(userMessage, systemMessage=null, profile="openai-gpt-4o", parameters=null)`
- `chatStream(messages, profile="openai-gpt-4o", parameters=null)`
- `chatComplete(messages, profile="openai-gpt-4o", parameters=null)`
- `getAvailableModels()`
- `getModelCapabilities(profile)`
- `createCreativeParams(level="medium")`
- `createDeterministicParams(seed=42)`
- `createFocusedParams(level="medium")`
- `createJsonResponseParams()`

## Error Handling

Both clients provide comprehensive error handling:

```python
# Python
try:
    response = client.simple_chat("Hello")
except ValueError as e:
    print(f"Invalid input: {e}")
except Exception as e:
    print(f"API error: {e}")
```

```javascript
// JavaScript
try {
    const response = await client.simpleChat("Hello");
} catch (error) {
    console.error("Error:", error.message);
}
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

## License

This project is licensed under the MIT License.

## Support

For questions or issues, please open an issue in the GitHub repository or contact the Grazie team. 