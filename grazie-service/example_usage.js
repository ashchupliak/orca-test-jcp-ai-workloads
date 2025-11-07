#!/usr/bin/env node

/**
 * Example usage of the JavaScript Grazie client with async/await
 * Demonstrates various features including streaming, parameters, and metadata
 */

const GrazieClient = require('./grazie_client.js');

async function main() {
    try {
        // Initialize client
        const client = new GrazieClient(null, "staging");
        
        console.log("Available models:");
        const models = await client.getAvailableModels();
        for (const model of models.slice(0, 5)) {  // Show first 5
            console.log(`  - ${model}`);
        }
        
        console.log("\n" + "=".repeat(50));
        
        // Example 1: Simple chat with temperature parameter
        console.log("Example 1: Creative response with high temperature");
        const creativeParams = client.createCreativeParams("high");
        const response1 = await client.simpleChat(
            "Write a creative tagline for a space travel company",
            null,
            "openai-gpt-4o",
            creativeParams,
            "creative-tagline-example"
        );
        console.log(`Response: ${response1}`);
        
        console.log("\n" + "=".repeat(50));
        
        // Example 2: Deterministic response
        console.log("Example 2: Deterministic response with seed");
        const deterministicParams = client.createDeterministicParams(12345);
        const response2 = await client.simpleChat(
            "Explain quantum computing in one sentence",
            null,
            "openai-gpt-4o",
            deterministicParams,
            "quantum-explanation"
        );
        console.log(`Response: ${response2}`);
        
        console.log("\n" + "=".repeat(50));
        
        // Example 3: JSON response format
        console.log("Example 3: Structured JSON response");
        const jsonParams = client.createJsonResponseParams();
        const response3 = await client.simpleChat(
            "Return the latitude and longitude of Paris in JSON format",
            null,
            "openai-gpt-4o",
            jsonParams,
            "paris-coordinates"
        );
        console.log(`Response: ${response3}`);
        
        console.log("\n" + "=".repeat(50));
        
        // Example 4: Custom parameters
        console.log("Example 4: Custom parameters with length limit");
        const customParams = {
            temperature: 0.7,
            length: 50,  // Limit response to 50 tokens
            top_p: 0.9
        };
        const response4 = await client.simpleChat(
            "Explain artificial intelligence",
            null,
            "openai-gpt-4o",
            customParams,
            "ai-explanation-short"
        );
        console.log(`Response: ${response4}`);
        
        console.log("\n" + "=".repeat(50));
        
        // Example 5: Chat with metadata
        console.log("Example 5: Chat with response metadata");
        const messages = [
            { type: "system", content: "You are a helpful assistant." },
            { type: "user", content: "What's the weather like?" }
        ];
        
        const [content, metadata] = await client.chatStreamWithMetadata(
            messages,
            "openai-gpt-4o",
            { temperature: 0.8 },
            "weather-query"
        );
        
        console.log(`Content: ${content}`);
        console.log(`Metadata: ${JSON.stringify(metadata, null, 2)}`);
        
        console.log("\n" + "=".repeat(50));
        
        // Example 6: Streaming with parameters
        console.log("Example 6: Streaming response with custom parameters");
        const streamParams = {
            temperature: 1.2,
            top_k: 50,
            stop_token: '.'  // Stop at first period
        };
        
        const streamMessages = [
            { type: "user", content: "Tell me about machine learning" }
        ];
        
        console.log("Streaming response:");
        for await (const chunk of client.chatStream(streamMessages, "openai-gpt-4o", streamParams, "ml-explanation")) {
            if (chunk.type === "Content") {
                process.stdout.write(chunk.content || "");
            } else if (chunk.type === "FinishMetadata") {
                console.log(`\n[Finished: ${chunk.reason}]`);
            } else if (chunk.type === "QuotaMetadata") {
                const spent = chunk.spent?.amount || 'N/A';
                console.log(`[Tokens spent: ${spent}]`);
            }
        }
        
        console.log("\n" + "=".repeat(50));
        
        // Example 7: Using different models (if available)
        console.log("Example 7: Trying different models");
        const availableModels = await client.getAvailableModels();
        const preferredModels = ["openai-gpt-4o", "anthropic-claude-3-5-sonnet-20241022"];
        
        for (const model of preferredModels) {
            if (availableModels.includes(model)) {
                console.log(`\nTesting with ${model}:`);
                try {
                    const response = await client.simpleChat(
                        "Hello, introduce yourself briefly",
                        null,
                        model,
                        { temperature: 0.5 }
                    );
                    console.log(`${model}: ${response.slice(0, 100)}...`);
                } catch (error) {
                    console.log(`${model}: Error - ${error.message}`);
                }
            }
        }
        
    } catch (error) {
        console.error("Error:", error.message);
        console.error("Make sure you have set the GRAZIE_JWT_TOKEN or USER_JWT_TOKEN environment variable");
    }
}

// Run the main function
if (require.main === module) {
    main().catch(console.error);
}

module.exports = { main }; 