/**
 * JavaScript Grazie Client
 * Port of the Python GrazieClient with async/await and fetch API
 * Supports JWT authentication, streaming, and parameter configuration
 */

class GrazieClient {
    static CONFIG_URLS = {
        production: "https://www.jetbrains.com/config/JetBrainsAIPlatform.json",
        staging: "https://config.stgn.jetbrains.ai"
    };

    static FALLBACK_ENDPOINTS = {
        production: "https://api.jetbrains.ai",
        staging: "https://api.app.stgn.grazie.aws.intellij.net"
    };

    static CHAT_ENDPOINTS = {
        staging: "/user/v5/llm/chat/stream/v8",
        production: "/user/v5/llm/chat/stream/v8"
    };

    constructor(jwtToken = null, environment = "staging") {
        this.jwtToken = jwtToken || process.env.USER_JWT_TOKEN || process.env.GRAZIE_JWT_TOKEN;
        this.environment = environment;
        this.baseUrl = null;
        this.profiles = {};
        this.modelCapabilities = {};
        this.chatAvailable = false;

        if (!this.jwtToken) {
            throw new Error("JWT token required");
        }

        this.initialized = false;
    }

    async initialize() {
        if (this.initialized) return;

        this.baseUrl = await this._discoverEndpoint();
        await this._validateToken();
        await this._loadProfiles();
        await this._testChatAvailability();
        
        this.initialized = true;
    }

    async _discoverEndpoint() {
        const configUrl = GrazieClient.CONFIG_URLS[this.environment];
        if (!configUrl) {
            return GrazieClient.FALLBACK_ENDPOINTS[this.environment] || GrazieClient.FALLBACK_ENDPOINTS.staging;
        }

        try {
            const response = await fetch(configUrl, {
                method: 'GET',
                timeout: 10000
            });

            if (!response.ok) {
                throw new Error(`Config fetch failed: ${response.status}`);
            }

            const config = await response.json();

            if (config.urls) {
                // Prefer deprecated endpoints (they have working APIs)
                for (const endpoint of config.urls) {
                    const url = endpoint.url || "";
                    if (url.includes("app.stgn.grazie.aws.intellij.net") || 
                        url.includes("app.prod.grazie.aws.intellij.net")) {
                        return url.replace(/\/$/, "");
                    }
                }

                // Fallback to non-deprecated endpoints
                const availableUrls = config.urls.filter(ep => !ep.deprecated);
                if (availableUrls.length > 0) {
                    return availableUrls[0].url.replace(/\/$/, "");
                }

                // Last resort: any endpoint
                const sortedUrls = config.urls.sort((a, b) => (a.priority || 999) - (b.priority || 999));
                if (sortedUrls.length > 0) {
                    return sortedUrls[0].url.replace(/\/$/, "");
                }
            }
        } catch (error) {
            console.warn("Failed to discover endpoint:", error);
        }

        return GrazieClient.FALLBACK_ENDPOINTS[this.environment] || GrazieClient.FALLBACK_ENDPOINTS.staging;
    }

    async _validateToken() {
        try {
            const response = await fetch(`${this.baseUrl}/user/v5/llm/profiles`, {
                method: 'GET',
                headers: this._getHeaders(),
                timeout: 10000
            });

            if (response.status === 401) {
                throw new Error("Invalid or expired JWT token");
            }

            if (!response.ok) {
                throw new Error(`Token validation failed: ${response.status}`);
            }
        } catch (error) {
            if (error.message.includes("401")) {
                throw new Error("Invalid or expired JWT token");
            }
            throw new Error(`Token validation failed: ${error.message}`);
        }
    }

    async _loadProfiles() {
        const response = await fetch(`${this.baseUrl}/user/v5/llm/profiles`, {
            method: 'GET',
            headers: this._getHeaders(),
            timeout: 10000
        });

        if (!response.ok) {
            throw new Error(`Failed to load profiles: ${response.status}`);
        }

        const data = await response.json();
        
        // Handle both direct list and {"profiles": [...]} formats
        const profilesData = Array.isArray(data) ? data : data.profiles || [];

        for (const profile of profilesData) {
            const profileId = profile.id;
            if (profileId) {
                this.profiles[profileId] = profile;
                this.modelCapabilities[profileId] = {
                    features: profile.features || [],
                    context_limit: profile.contextLimit || 0,
                    max_output_tokens: profile.maxOutputTokens || 0,
                    provider: profile.provider || "",
                    deprecated: profile.deprecated || false
                };
            }
        }
    }

    async _testChatAvailability() {
        try {
            const chatEndpoint = GrazieClient.CHAT_ENDPOINTS[this.environment] || "/user/v5/llm/chat/stream";
            const testPayload = {
                profile: "openai-gpt-4o",
                chat: {
                    messages: [{ type: "user_message", content: "test" }]
                }
            };

            const response = await fetch(`${this.baseUrl}${chatEndpoint}`, {
                method: 'POST',
                headers: this._getHeaders(),
                body: JSON.stringify(testPayload),
                timeout: 5000
            });

            this.chatAvailable = response.ok;
            
            // Close the stream
            if (response.body) {
                const reader = response.body.getReader();
                reader.cancel();
            }
        } catch (error) {
            this.chatAvailable = false;
        }
    }

    _getHeaders() {
        if (!this.jwtToken) {
            throw new Error("JWT token required");
        }

        return {
            "Content-Type": "application/json",
            "Grazie-Agent": JSON.stringify({ name: "javascript-client", version: "1.0" }),
            "Grazie-Authenticate-JWT": this.jwtToken
        };
    }

    async getAvailableModels() {
        if (!this.initialized) await this.initialize();
        
        return Object.keys(this.modelCapabilities).filter(
            modelId => !this.modelCapabilities[modelId].deprecated
        );
    }

    async getModelCapabilities(profile) {
        if (!this.initialized) await this.initialize();
        
        if (!(profile in this.modelCapabilities)) {
            throw new Error(`Model '${profile}' not available`);
        }
        return this.modelCapabilities[profile];
    }

    async validateModelForChat(profile) {
        const caps = await this.getModelCapabilities(profile);
        return caps.features.includes("Chat");
    }

    async isChatAvailable() {
        if (!this.initialized) await this.initialize();
        return this.chatAvailable;
    }

    async *chatStream(messages, profile = "openai-gpt-4o", parameters = null, prompt = null) {
        if (!this.initialized) await this.initialize();
        
        if (!this.chatAvailable) {
            throw new Error("Chat functionality is not available in this environment");
        }

        if (!(await this.validateModelForChat(profile))) {
            throw new Error(`Model '${profile}' does not support chat`);
        }

        const chatEndpoint = GrazieClient.CHAT_ENDPOINTS[this.environment] || "/user/v5/llm/chat/stream/v8";
        const url = `${this.baseUrl}${chatEndpoint}`;

        const payload = {
            profile: profile,
            chat: { messages: messages }
        };

        if (prompt) {
            payload.prompt = prompt;
        }

        const paramsData = this._createParametersData(parameters);
        if (paramsData) {
            payload.parameters = paramsData;
        }

        const response = await fetch(url, {
            method: 'POST',
            headers: this._getHeaders(),
            body: JSON.stringify(payload)
        });

        if (!response.ok) {
            throw new Error(`Chat stream failed: ${response.status}`);
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder();

        try {
            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                const chunk = decoder.decode(value, { stream: true });
                const lines = chunk.split('\n');

                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        const dataStr = line.slice(6);
                        if (dataStr.trim() === 'end') {
                            return;
                        }
                        try {
                            const data = JSON.parse(dataStr);
                            yield data;
                        } catch (error) {
                            console.warn("Failed to parse chunk:", dataStr);
                        }
                    }
                }
            }
        } finally {
            reader.releaseLock();
        }
    }

    async chatComplete(messages, profile = "openai-gpt-4o", parameters = null, prompt = null) {
        const contentParts = [];
        
        for await (const chunk of this.chatStream(messages, profile, parameters, prompt)) {
            if (chunk.type === "Content") {
                contentParts.push(chunk.content || "");
            }
        }

        return contentParts.join("");
    }

    async simpleChat(userMessage, systemMessage = null, profile = "openai-gpt-4o", parameters = null, prompt = null) {
        const messages = [];
        
        if (systemMessage) {
            messages.push({ type: "system", content: systemMessage });
        }
        
        messages.push({ type: "user", content: userMessage });

        return await this.chatComplete(messages, profile, parameters, prompt);
    }

    _createParametersData(parameters) {
        if (!parameters) return null;

        const parametersList = [];

        for (const [key, value] of Object.entries(parameters)) {
            if (key === "temperature") {
                parametersList.push({
                    name: "temperature",
                    value: Math.max(0, Math.min(2, value))
                });
            } else if (key === "top_p") {
                parametersList.push({
                    name: "top_p",
                    value: Math.max(0, Math.min(1, value))
                });
            } else if (key === "top_k") {
                parametersList.push({
                    name: "top_k",
                    value: Math.max(1, Math.min(100, Math.floor(value)))
                });
            } else if (key === "length") {
                parametersList.push({
                    name: "length",
                    value: Math.max(1, Math.floor(value))
                });
            } else if (key === "max_tokens") {
                parametersList.push({
                    name: "max_tokens",
                    value: Math.max(1, Math.floor(value))
                });
            } else if (key === "seed") {
                parametersList.push({
                    name: "seed",
                    value: Math.floor(value)
                });
            } else if (key === "stop_token") {
                parametersList.push({
                    name: "stop_sequences",
                    value: [value]
                });
            } else if (key === "format") {
                parametersList.push({
                    name: "format",
                    value: value
                });
            }
        }

        return parametersList.length > 0 ? { parameters: parametersList } : null;
    }

    createDeterministicParams(seed = 42) {
        return {
            temperature: 0.0,
            top_p: 1.0,
            seed: seed
        };
    }

    createCreativeParams(creativityLevel = "medium") {
        const levelMap = {
            low: { temperature: 0.7, top_p: 0.8 },
            medium: { temperature: 1.0, top_p: 0.9 },
            high: { temperature: 1.3, top_p: 0.95 }
        };

        return levelMap[creativityLevel] || levelMap.medium;
    }

    createFocusedParams(focusLevel = "medium") {
        const levelMap = {
            low: { temperature: 0.5, top_p: 0.7, top_k: 50 },
            medium: { temperature: 0.3, top_p: 0.6, top_k: 40 },
            high: { temperature: 0.1, top_p: 0.5, top_k: 30 }
        };

        return levelMap[focusLevel] || levelMap.medium;
    }

    createJsonResponseParams() {
        return {
            temperature: 0.2,
            format: "json"
        };
    }

    async chatStreamWithMetadata(messages, profile = "openai-gpt-4o", parameters = null, prompt = null) {
        const chunks = [];
        const contentParts = [];

        for await (const chunk of this.chatStream(messages, profile, parameters, prompt)) {
            chunks.push(chunk);
            if (chunk.type === "Content") {
                contentParts.push(chunk.content || "");
            }
        }

        const content = contentParts.join("");
        const metadata = this.extractResponseMetadata(chunks);

        return [content, metadata];
    }

    extractResponseMetadata(streamChunks) {
        const metadata = {
            finish_reason: null,
            tokens_spent: 0,
            model_used: null,
            request_id: null,
            response_time: null
        };

        for (const chunk of streamChunks) {
            if (chunk.type === "FinishMetadata") {
                metadata.finish_reason = chunk.reason;
            } else if (chunk.type === "QuotaMetadata") {
                const spent = chunk.spent || {};
                metadata.tokens_spent = spent.amount || 0;
            } else if (chunk.type === "ModelMetadata") {
                metadata.model_used = chunk.model;
            } else if (chunk.request_id) {
                metadata.request_id = chunk.request_id;
            } else if (chunk.response_time) {
                metadata.response_time = chunk.response_time;
            }
        }

        return metadata;
    }
}

// Export for both CommonJS and ES modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = GrazieClient;
} else if (typeof window !== 'undefined') {
    window.GrazieClient = GrazieClient;
} 