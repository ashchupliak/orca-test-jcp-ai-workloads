import json
import os
import requests
from typing import Dict, List, Optional, Iterator, Any, Union


class GrazieClient:
    CONFIG_URLS = {
        "production": "https://www.jetbrains.com/config/JetBrainsAIPlatform.json",
        "staging": "https://config.stgn.jetbrains.ai"
    }
    
    FALLBACK_ENDPOINTS = {
        "production": "https://api.jetbrains.ai",
        "staging": "https://api.app.stgn.grazie.aws.intellij.net"
    }
    
    # Updated API endpoints to match latest documentation
    CHAT_ENDPOINTS = {
        "staging": "/user/v5/llm/chat/stream/v8",
        "production": "/user/v5/llm/chat/stream/v8"
    }
    
    def __init__(self, jwt_token: Optional[str] = None, environment: str = "staging"):
        self.jwt_token = jwt_token or os.getenv('USER_JWT_TOKEN') or os.getenv('GRAZIE_JWT_TOKEN')
        self.environment = environment
        self.base_url = self._discover_endpoint()
        self.profiles = {}
        self.model_capabilities = {}
        self.chat_available = False
        
        if not self.jwt_token:
            raise ValueError("JWT token required")
        
        self._validate_token()
        self._load_profiles()
        self._test_chat_availability()
    
    def _discover_endpoint(self) -> str:
        config_url = self.CONFIG_URLS.get(self.environment)
        if not config_url:
            return self.FALLBACK_ENDPOINTS.get(self.environment, self.FALLBACK_ENDPOINTS["staging"])
        
        try:
            response = requests.get(config_url, timeout=10)
            response.raise_for_status()
            config = response.json()
            
            if "urls" in config:
                # Always prefer deprecated endpoints since they have working APIs
                for endpoint in config["urls"]:
                    url = endpoint.get("url", "")
                    if ("app.stgn.grazie.aws.intellij.net" in url or 
                        "app.prod.grazie.aws.intellij.net" in url):
                        return url.rstrip("/")
                
                # Fallback to first available non-deprecated
                available_urls = [ep for ep in config["urls"] if not ep.get("deprecated", False)]
                if available_urls:
                    return available_urls[0]["url"].rstrip("/")
                
                # Last resort: any endpoint
                all_urls = sorted(config["urls"], key=lambda x: x.get("priority", 999))
                if all_urls:
                    return all_urls[0]["url"].rstrip("/")
        except Exception:
            pass
        
        return self.FALLBACK_ENDPOINTS.get(self.environment, self.FALLBACK_ENDPOINTS["staging"])
    
    def _validate_token(self):
        try:
            response = requests.get(
                f"{self.base_url}/user/v5/llm/profiles",
                headers=self._get_headers(),
                timeout=10
            )
            if response.status_code == 401:
                raise ValueError("Invalid or expired JWT token")
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            if "401" in str(e):
                raise ValueError("Invalid or expired JWT token")
            raise ValueError(f"Token validation failed: {e}")
    
    def _load_profiles(self):
        response = requests.get(
            f"{self.base_url}/user/v5/llm/profiles",
            headers=self._get_headers(),
            timeout=10
        )
        response.raise_for_status()
        
        data = response.json()
        # Handle both direct list and {"profiles": [...]} formats
        if isinstance(data, dict) and "profiles" in data:
            profiles_data = data["profiles"]
        elif isinstance(data, list):
            profiles_data = data
        else:
            raise ValueError(f"Unexpected profiles response format: {type(data)}")
        
        for profile in profiles_data:
            profile_id = profile.get("id")
            if profile_id:
                self.profiles[profile_id] = profile
                self.model_capabilities[profile_id] = {
                    "features": profile.get("features", []),
                    "context_limit": profile.get("contextLimit", 0),
                    "max_output_tokens": profile.get("maxOutputTokens", 0),
                    "provider": profile.get("provider", ""),
                    "deprecated": profile.get("deprecated", False)
                }
    
    def _test_chat_availability(self):
        try:
            chat_endpoint = self.CHAT_ENDPOINTS.get(self.environment, "/user/v5/llm/chat/stream")
            test_payload = {
                "profile": "openai-gpt-4o",
                "chat": {"messages": [{"type": "user_message", "content": "test"}]}
            }
            response = requests.post(
                f"{self.base_url}{chat_endpoint}",
                headers=self._get_headers(),
                json=test_payload,
                timeout=5,
                stream=True
            )
            self.chat_available = response.status_code == 200
            response.close()
        except Exception:
            self.chat_available = False
    
    def _get_headers(self) -> Dict[str, str]:
        if not self.jwt_token:
            raise ValueError("JWT token required")
        return {
            "Content-Type": "application/json",
            "Grazie-Agent": json.dumps({"name": "python-client", "version": "2.0"}),
            "Grazie-Authenticate-JWT": self.jwt_token
        }
    
    def get_available_models(self) -> List[str]:
        return [model_id for model_id, caps in self.model_capabilities.items() 
                if not caps["deprecated"]]
    
    def get_model_capabilities(self, profile: str) -> Dict[str, Any]:
        if profile not in self.model_capabilities:
            raise ValueError(f"Model '{profile}' not available")
        return self.model_capabilities[profile]
    
    def validate_model_for_chat(self, profile: str) -> bool:
        caps = self.get_model_capabilities(profile)
        return "Chat" in caps["features"]
    
    def is_chat_available(self) -> bool:
        return self.chat_available
    
    def chat_stream(self, 
                   messages: List[Dict[str, str]], 
                   profile: str = "openai-gpt-4o",
                   parameters: Optional[Dict[str, Any]] = None,
                   prompt: Optional[str] = None) -> Iterator[Dict[str, Any]]:
        """
        Stream chat completions with file attachment support.
        
        Args:
            messages: List of message dictionaries with 'type' and 'content' keys
            profile: Model profile ID
            parameters: Optional parameters for the model  
            prompt: Optional prompt for tracking
            attachments: Optional list of file attachments with format:
                [{"name": "file.png", "type": "image/png", "content": "base64_data"}]
        
        Yields:
            Dictionary chunks from the streaming response
        """
        if not self.chat_available:
            raise ValueError("Chat functionality is not available in this environment")
        
        if not self.validate_model_for_chat(profile):
            raise ValueError(f"Model '{profile}' does not support chat")
        
        chat_endpoint = self.CHAT_ENDPOINTS.get(self.environment, "/user/v5/llm/chat/stream/v8")
        url = f"{self.base_url}{chat_endpoint}"
        
        payload = {
            "profile": profile,
            "chat": {"messages": messages}
        }
        
        # Add prompt if provided (for tracking/identification)
        if prompt:
            payload["prompt"] = prompt
        
        # Add parameters if provided
        params_data = self._create_parameters_data(parameters)
        if params_data:
            payload["parameters"] = params_data
        
        # Debug logging for request payload
        print(f"DEBUG: Sending request to {url}")
        print(f"DEBUG: Profile: {profile}")
        print(f"DEBUG: Payload: {json.dumps(payload, indent=2)}")
        
        response = requests.post(
            url,
            headers=self._get_headers(),
            json=payload,
            stream=True
        )
        
        # Enhanced error handling with response body
        if not response.ok:
            try:
                error_body = response.text
                print(f"DEBUG: Error response body: {error_body}")
            except:
                error_body = "Could not read error response"
            
            raise requests.exceptions.HTTPError(
                f"{response.status_code} Client Error: {response.reason} for url: {response.url}\n"
                f"Response body: {error_body}"
            )
        
        for line in response.iter_lines(decode_unicode=True):
            if line.startswith('data: '):
                data_str = line[6:]
                if data_str.strip() == 'end':
                    break
                try:
                    chunk = json.loads(data_str)
                    yield chunk
                    
                    # Check for finish condition
                    if chunk.get("type") == "FinishMetadata":
                        break
                        
                except json.JSONDecodeError:
                    continue
    
    def chat_complete(self, 
                     messages: List[Dict[str, str]], 
                     profile: str = "openai-gpt-4o",
                     parameters: Optional[Dict[str, Any]] = None,
                     prompt: Optional[str] = None) -> str:
        content_parts = []
        for chunk in self.chat_stream(messages, profile, parameters, prompt):
            if chunk.get("type") == "Content":
                content_parts.append(chunk.get("content", ""))
        return "".join(content_parts)
    
    def simple_chat(self, 
                   user_message: str, 
                   system_message: Optional[str] = None,
                   profile: str = "openai-gpt-4o",
                   parameters: Optional[Dict[str, Any]] = None,
                   prompt: Optional[str] = None) -> str:
        messages = []
        if system_message:
            messages.append({"type": "system_message", "content": system_message})
        messages.append({"type": "user_message", "content": user_message})
        return self.chat_complete(messages, profile, parameters, prompt)

    def _create_parameters_data(self, parameters: Optional[Dict[str, Any]]) -> Optional[Dict[str, List[Dict[str, Any]]]]:
        """Convert parameters dict to the API format with data array."""
        if not parameters:
            return None
        
        data = []
        for key, value in parameters.items():
            # Map parameter names to their FQDNs and determine types
            param_mapping = {
                'temperature': ('llm.parameters.temperature', 'double'),
                'top_p': ('llm.parameters.top-p', 'double'),
                'top_k': ('llm.parameters.top-k', 'int'),
                'length': ('llm.parameters.length', 'int'),
                'max_tokens': ('llm.parameters.length', 'int'),  # Alias for length
                'stop_token': ('llm.parameters.stop-token', 'text'),
                'seed': ('llm.parameters.seed', 'int'),
                'dimension': ('llm.parameters.dimension', 'int'),
                'response_format': ('llm.parameters.response-format', 'json'),
                'predicted_output': ('llm.parameters.predicted-output', 'text'),
                'reasoning_effort': ('llm.parameters.reasoning-effort', 'text'),
                'number_of_choices': ('llm.parameters.number-of-choices', 'int'),
                'cache_points': ('llm.parameters.cache-points', 'json'),
                'tools': ('llm.parameters.tools', 'json'),
                'tool_choice': ('llm.parameters.tool-choice', 'json')
            }
            
            if key in param_mapping:
                fqdn, param_type = param_mapping[key]
                data.extend([
                    {"type": param_type, "fqdn": fqdn},
                    {"type": param_type, "value": value}
                ])
            else:
                # For unknown parameters, try to infer type
                if isinstance(value, bool):
                    param_type = "bool"
                elif isinstance(value, int):
                    param_type = "int"
                elif isinstance(value, float):
                    param_type = "double"
                elif isinstance(value, (dict, list)):
                    param_type = "json"
                else:
                    param_type = "text"
                
                data.extend([
                    {"type": param_type, "fqdn": key},
                    {"type": param_type, "value": value}
                ])
        
        return {"data": data} if data else None

    def create_deterministic_params(self, seed: int = 42) -> Dict[str, Any]:
        """Create parameters for deterministic output."""
        return {
            'temperature': 0.0,
            'seed': seed
        }

    def create_creative_params(self, creativity_level: str = "medium") -> Dict[str, Any]:
        """Create parameters for creative output.
        
        Args:
            creativity_level: "low", "medium", or "high"
        """
        if creativity_level == "low":
            return {'temperature': 0.7, 'top_p': 0.8}
        elif creativity_level == "medium":
            return {'temperature': 1.0, 'top_p': 0.9}
        elif creativity_level == "high":
            return {'temperature': 1.3, 'top_p': 0.95}
        else:
            raise ValueError("creativity_level must be 'low', 'medium', or 'high'")

    def create_focused_params(self, focus_level: str = "medium") -> Dict[str, Any]:
        """Create parameters for focused/deterministic output.
        
        Args:
            focus_level: "low", "medium", or "high"
        """
        if focus_level == "low":
            return {'temperature': 0.8, 'top_k': 40}
        elif focus_level == "medium":
            return {'temperature': 0.6, 'top_k': 20}
        elif focus_level == "high":
            return {'temperature': 0.3, 'top_k': 10}
        else:
            raise ValueError("focus_level must be 'low', 'medium', or 'high'")

    def create_json_response_params(self) -> Dict[str, Any]:
        """Create parameters to ensure JSON response format."""
        return {
            'response_format': {"type": "json"}
        }

    def extract_response_metadata(self, stream_chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Extract metadata from stream response chunks."""
        metadata = {
            'finish_reason': None,
            'quota_info': None,
            'content_length': 0,
            'token_count': None
        }
        
        content_chars = 0
        for chunk in stream_chunks:
            chunk_type = chunk.get('type')
            
            if chunk_type == "Content":
                content_chars += len(chunk.get('content', ''))
            elif chunk_type == "FinishMetadata":
                metadata['finish_reason'] = chunk.get('reason')
            elif chunk_type == "QuotaMetadata":
                metadata['quota_info'] = {
                    'spent': chunk.get('spent', {}),
                    'updated': chunk.get('updated', {})
                }
        
        metadata['content_length'] = content_chars
        return metadata

    def chat_stream_with_metadata(self, 
                                messages: List[Dict[str, str]], 
                                profile: str = "openai-gpt-4o",
                                parameters: Optional[Dict[str, Any]] = None,
                                prompt: Optional[str] = None) -> tuple[str, Dict[str, Any]]:
        """Chat with streaming and return both content and metadata."""
        chunks = []
        content_parts = []
        
        for chunk in self.chat_stream(messages, profile, parameters, prompt):
            chunks.append(chunk)
            if chunk.get("type") == "Content":
                content_parts.append(chunk.get("content", ""))
        
        content = "".join(content_parts)
        metadata = self.extract_response_metadata(chunks)
        
        return content, metadata 