import os
from typing import Dict, List, Optional, Iterator, Any, Union
from grazie.api.client.gateway import AuthType, GrazieApiGatewayClient, GrazieAgent
from grazie.api.client.endpoints import GrazieApiGatewayUrls
from grazie.api.client.profiles import LLMProfileIDs
from grazie.api.client.llm.v5.requests import LLMRequest
from grazie.api.client.llm.v5.responses import LLMResponse
from grazie.api.client.llm.v5.entities import LLMMessageContent, LLMMessageRole, LLMMessage
from grazie.api.client.llm.v5.parameters import LLMParameters


class GrazieSDKClient:
    """
    A Grazie client using the official SDK instead of direct HTTP calls.
    Provides similar functionality to the original client but with SDK benefits.
    """
    
    def __init__(self, jwt_token: Optional[str] = None, environment: str = "staging"):
        self.jwt_token = jwt_token or os.getenv('GRAZIE_JWT_TOKEN') or os.getenv('USER_JWT_TOKEN')
        self.environment = environment
        
        if not self.jwt_token:
            raise ValueError("JWT token required. Set GRAZIE_JWT_TOKEN environment variable or pass jwt_token parameter.")
        
        # Initialize the SDK client
        self.client = GrazieApiGatewayClient(
            url=GrazieApiGatewayUrls.STAGING if environment == "staging" else GrazieApiGatewayUrls.PRODUCTION,
            grazie_jwt_token=self.jwt_token,
            auth_type=AuthType.USER,
            grazie_agent=GrazieAgent(name="grazie-sdk-client", version="1.0")
        )
        
        # Cache for profiles and capabilities
        self.profiles = {}
        self.model_capabilities = {}
        self._load_profiles()
    
    def _load_profiles(self):
        """Load available profiles and their capabilities from the API."""
        try:
            # Get profiles using the SDK
            profiles_response = self.client.profiles()
            
            for profile in profiles_response.profiles:
                profile_id = profile.id
                self.profiles[profile_id] = profile
                self.model_capabilities[profile_id] = {
                    "features": profile.features,
                    "context_limit": profile.context_limit,
                    "max_output_tokens": profile.max_output_tokens,
                    "provider": profile.provider,
                    "deprecated": profile.deprecated
                }
        except Exception as e:
            print(f"Warning: Could not load profiles: {e}")
    
    def get_available_models(self) -> List[str]:
        """Get list of available model IDs."""
        return [model_id for model_id, caps in self.model_capabilities.items() 
                if not caps.get("deprecated", False)]
    
    def get_model_capabilities(self, profile: str) -> Dict[str, Any]:
        """Get capabilities for a specific model."""
        if profile not in self.model_capabilities:
            raise ValueError(f"Model '{profile}' not available")
        return self.model_capabilities[profile]
    
    def validate_model_for_chat(self, profile: str) -> bool:
        """Check if a model supports chat functionality."""
        caps = self.get_model_capabilities(profile)
        return "Chat" in caps.get("features", [])
    
    def _convert_messages_to_sdk_format(self, messages: List[Dict[str, str]]) -> List[LLMMessage]:
        """Convert message format to SDK format."""
        sdk_messages = []
        for msg in messages:
            # Map message types to SDK roles
            role_mapping = {
                "user": LLMMessageRole.USER,
                "system": LLMMessageRole.SYSTEM,
                "assistant": LLMMessageRole.ASSISTANT,
                "user_message": LLMMessageRole.USER,
                "assistant_message": LLMMessageRole.ASSISTANT
            }
            
            msg_type = msg.get("type", "user")
            role = role_mapping.get(msg_type, LLMMessageRole.USER)
            
            sdk_messages.append(
                LLMMessage(
                    role=role,
                    content=LLMMessageContent(value=msg.get("content", ""))
                )
            )
        
        return sdk_messages
    
    def _create_llm_parameters(self, parameters: Optional[Dict[str, Any]]) -> Optional[LLMParameters]:
        """Create LLM parameters from dict."""
        if not parameters:
            return None
        
        # Create parameters object with SDK
        llm_params = LLMParameters()
        
        # Set common parameters
        if "temperature" in parameters:
            llm_params.temperature = parameters["temperature"]
        if "top_p" in parameters:
            llm_params.top_p = parameters["top_p"]
        if "top_k" in parameters:
            llm_params.top_k = parameters["top_k"]
        if "max_tokens" in parameters:
            llm_params.max_tokens = parameters["max_tokens"]
        if "seed" in parameters:
            llm_params.seed = parameters["seed"]
        if "stop_token" in parameters:
            llm_params.stop_sequences = [parameters["stop_token"]]
        
        return llm_params
    
    def chat_stream(self, 
                   messages: List[Dict[str, str]], 
                   profile: str = "anthropic-claude-3-5-sonnet-20241022",  # Default to Sonnet 4
                   parameters: Optional[Dict[str, Any]] = None,
                   prompt: Optional[str] = None) -> Iterator[Dict[str, Any]]:
        """
        Stream chat completions using the SDK.
        
        Args:
            messages: List of message dictionaries with 'type' and 'content' keys
            profile: Model profile ID (defaults to Claude Sonnet 4)
            parameters: Optional parameters for the model
            prompt: Optional prompt for tracking
        
        Yields:
            Dictionary chunks from the streaming response
        """
        if not self.validate_model_for_chat(profile):
            raise ValueError(f"Model '{profile}' does not support chat")
        
        # Convert messages to SDK format
        sdk_messages = self._convert_messages_to_sdk_format(messages)
        
        # Create parameters
        llm_params = self._create_llm_parameters(parameters)
        
        # Create the request
        request = LLMRequest(
            profile=profile,
            messages=sdk_messages,
            parameters=llm_params
        )
        
        # Stream the response
        try:
            response_stream = self.client.llm_stream(request)
            
            for chunk in response_stream:
                # Convert SDK response to compatible format
                if hasattr(chunk, 'content') and chunk.content:
                    yield {
                        "type": "Content",
                        "content": chunk.content
                    }
                elif hasattr(chunk, 'finish_reason'):
                    yield {
                        "type": "FinishMetadata",
                        "reason": chunk.finish_reason
                    }
                elif hasattr(chunk, 'usage'):
                    yield {
                        "type": "QuotaMetadata",
                        "spent": chunk.usage.__dict__ if chunk.usage else {},
                        "updated": {}
                    }
                
        except Exception as e:
            raise RuntimeError(f"Chat streaming failed: {e}")
    
    def chat_complete(self, 
                     messages: List[Dict[str, str]], 
                     profile: str = "anthropic-claude-3-5-sonnet-20241022",  # Default to Sonnet 4
                     parameters: Optional[Dict[str, Any]] = None,
                     prompt: Optional[str] = None) -> str:
        """
        Complete chat request and return the full response.
        
        Args:
            messages: List of message dictionaries
            profile: Model profile ID (defaults to Claude Sonnet 4)
            parameters: Optional parameters
            prompt: Optional prompt for tracking
        
        Returns:
            Complete response content as string
        """
        content_parts = []
        for chunk in self.chat_stream(messages, profile, parameters, prompt):
            if chunk.get("type") == "Content":
                content_parts.append(chunk.get("content", ""))
        return "".join(content_parts)
    
    def simple_chat(self, 
                   user_message: str, 
                   system_message: Optional[str] = None,
                   profile: str = "anthropic-claude-3-5-sonnet-20241022",  # Default to Sonnet 4
                   parameters: Optional[Dict[str, Any]] = None,
                   prompt: Optional[str] = None) -> str:
        """
        Simple chat interface with a single user message.
        
        Args:
            user_message: The user's message
            system_message: Optional system message
            profile: Model profile ID (defaults to Claude Sonnet 4)
            parameters: Optional parameters
            prompt: Optional prompt for tracking
        
        Returns:
            Response content as string
        """
        messages = []
        if system_message:
            messages.append({"type": "system", "content": system_message})
        messages.append({"type": "user", "content": user_message})
        return self.chat_complete(messages, profile, parameters, prompt)
    
    def chat_stream_with_metadata(self, 
                                messages: List[Dict[str, str]], 
                                profile: str = "anthropic-claude-3-5-sonnet-20241022",  # Default to Sonnet 4
                                parameters: Optional[Dict[str, Any]] = None,
                                prompt: Optional[str] = None) -> tuple[str, Dict[str, Any]]:
        """
        Chat with streaming and return both content and metadata.
        
        Args:
            messages: List of message dictionaries
            profile: Model profile ID (defaults to Claude Sonnet 4)
            parameters: Optional parameters
            prompt: Optional prompt for tracking
        
        Returns:
            Tuple of (content, metadata)
        """
        chunks = []
        content_parts = []
        
        for chunk in self.chat_stream(messages, profile, parameters, prompt):
            chunks.append(chunk)
            if chunk.get("type") == "Content":
                content_parts.append(chunk.get("content", ""))
        
        content = "".join(content_parts)
        metadata = self.extract_response_metadata(chunks)
        
        return content, metadata
    
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
    
    # Helper methods for creating common parameter sets
    def create_deterministic_params(self, seed: int = 42) -> Dict[str, Any]:
        """Create parameters for deterministic output."""
        return {
            'temperature': 0.0,
            'seed': seed
        }
    
    def create_creative_params(self, creativity_level: str = "medium") -> Dict[str, Any]:
        """Create parameters for creative output."""
        if creativity_level == "low":
            return {'temperature': 0.7, 'top_p': 0.8}
        elif creativity_level == "medium":
            return {'temperature': 1.0, 'top_p': 0.9}
        elif creativity_level == "high":
            return {'temperature': 1.3, 'top_p': 0.95}
        else:
            raise ValueError("creativity_level must be 'low', 'medium', or 'high'")
    
    def create_focused_params(self, focus_level: str = "medium") -> Dict[str, Any]:
        """Create parameters for focused/deterministic output."""
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
    
    # Sonnet 4 specific methods
    def sonnet4_chat(self, 
                    user_message: str, 
                    system_message: Optional[str] = None,
                    parameters: Optional[Dict[str, Any]] = None) -> str:
        """
        Chat specifically with Claude Sonnet 4 model.
        
        Args:
            user_message: The user's message
            system_message: Optional system message
            parameters: Optional parameters
        
        Returns:
            Response content as string
        """
        return self.simple_chat(
            user_message=user_message,
            system_message=system_message,
            profile="anthropic-claude-3-5-sonnet-20241022",  # Sonnet 4
            parameters=parameters
        )
    
    def sonnet4_stream(self, 
                      user_message: str, 
                      system_message: Optional[str] = None,
                      parameters: Optional[Dict[str, Any]] = None) -> Iterator[Dict[str, Any]]:
        """
        Stream chat with Claude Sonnet 4 model.
        
        Args:
            user_message: The user's message
            system_message: Optional system message
            parameters: Optional parameters
        
        Yields:
            Dictionary chunks from the streaming response
        """
        messages = []
        if system_message:
            messages.append({"type": "system", "content": system_message})
        messages.append({"type": "user", "content": user_message})
        
        yield from self.chat_stream(
            messages=messages,
            profile="anthropic-claude-3-5-sonnet-20241022",  # Sonnet 4
            parameters=parameters
        ) 