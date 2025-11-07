#!/usr/bin/env python3
"""
Flask web app for Grazie AI client with advanced UI interface
"""

from flask import Flask, render_template, request, jsonify, Response
import json
import traceback
import base64
import zipfile
import tempfile
import os
import io
import mimetypes
from pathlib import Path
from grazie_client import GrazieClient
import logging

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max file size for video support

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/models', methods=['POST'])
def get_models():
    """Get available models for the specified environment and token"""
    try:
        data = request.get_json()
        token = data.get('token')
        environment = data.get('environment', 'staging')
        
        logger.info(f"Loading models for environment: {environment}")
        
        if not token:
            return jsonify({'error': 'Token is required'}), 400
        
        client = GrazieClient(jwt_token=token, environment=environment)
        models = client.get_available_models()
        
        logger.info(f"Found {len(models)} models")
        
        # Get model details
        model_details = []
        for model in models:
            try:
                capabilities = client.get_model_capabilities(model)
                model_details.append({
                    'id': model,
                    'name': model.replace('-', ' ').title(),
                    'provider': capabilities.get('provider', 'Grazie'),
                    'features': capabilities.get('features', []),
                    'context_limit': capabilities.get('context_limit', 0),
                    'supports_chat': 'Chat' in capabilities.get('features', []),
                    'supports_vision': 'Vision' in capabilities.get('features', []),
                    'supports_audio': 'Audio' in capabilities.get('features', [])
                })
            except Exception as e:
                logger.warning(f"Failed to get capabilities for model {model}: {e}")
                model_details.append({
                    'id': model,
                    'name': model.replace('-', ' ').title(),
                    'provider': 'Grazie',
                    'features': ['Chat'],
                    'context_limit': 0,
                    'supports_chat': True,
                    'supports_vision': False,
                    'supports_audio': False
                })
        
        logger.info(f"Returning {len(model_details)} model details")
        return jsonify({'models': model_details})
    
    except Exception as e:
        logger.error(f"Error in get_models: {str(e)}\n{traceback.format_exc()}")
        return jsonify({'error': str(e)}), 500

def process_zip_file(file_data):
    """Extract and analyze ZIP file contents"""
    try:
        logger.info(f"Processing ZIP file: {file_data['name']}")
        
        # Decode base64 file content
        zip_content = base64.b64decode(file_data['content'])
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as temp_file:
            temp_file.write(zip_content)
            temp_file_path = temp_file.name
        
        file_contents = {}
        file_summary = []
        
        try:
            with zipfile.ZipFile(temp_file_path, 'r') as zip_ref:
                # Get list of files
                file_list = zip_ref.namelist()
                logger.info(f"ZIP contains {len(file_list)} items")
                
                for file_path in file_list:
                    if not file_path.endswith('/'):  # Skip directories
                        try:
                            # Read file content
                            with zip_ref.open(file_path) as file:
                                content = file.read()
                                
                                # Try to decode as text for common file types
                                file_ext = Path(file_path).suffix.lower()
                                if file_ext in ['.txt', '.md', '.py', '.js', '.html', '.css', '.json', '.xml', '.csv', '.yml', '.yaml', '.config']:
                                    try:
                                        text_content = content.decode('utf-8')
                                        file_contents[file_path] = {
                                            'type': 'text',
                                            'content': text_content,
                                            'size': len(content)
                                        }
                                    except UnicodeDecodeError:
                                        file_contents[file_path] = {
                                            'type': 'binary',
                                            'content': f"Binary file ({len(content)} bytes)",
                                            'size': len(content)
                                        }
                                else:
                                    file_contents[file_path] = {
                                        'type': 'binary',
                                        'content': f"Binary file ({len(content)} bytes)",
                                        'size': len(content)
                                    }
                                
                                file_summary.append({
                                    'path': file_path,
                                    'size': len(content),
                                    'type': file_contents[file_path]['type']
                                })
                        except Exception as e:
                            logger.warning(f"Error processing file {file_path}: {e}")
                            file_summary.append({
                                'path': file_path,
                                'size': 0,
                                'type': 'error',
                                'error': str(e)
                            })
        finally:
            # Clean up temporary file
            os.unlink(temp_file_path)
        
        result = {
            'file_count': len(file_summary),
            'total_size': sum(f['size'] for f in file_summary),
            'file_summary': file_summary,
            'file_contents': file_contents
        }
        
        logger.info(f"ZIP processing complete: {result['file_count']} files, {result['total_size']} total bytes")
        return result
    
    except Exception as e:
        logger.error(f"Failed to process ZIP file: {e}")
        return {'error': f"Failed to process ZIP file: {str(e)}"}

def prepare_message_with_files(message, files):
    """Prepare message content including file analysis"""
    if not files:
        logger.info("No files to process")
        return message
    
    logger.info(f"Preparing message with {len(files)} files")
    file_analysis = []
    
    for file_data in files:
        logger.info(f"Processing file: {file_data['name']} ({file_data['type']}, {file_data.get('size', 0)} bytes)")
        
        analysis = f"\n\n📎 **File: {file_data['name']}**\n"
        analysis += f"Type: {file_data['type']}\n"
        analysis += f"Size: {format_file_size(file_data.get('size', 0))}\n"
        
        # Handle ZIP files
        if file_data['name'].lower().endswith('.zip'):
            zip_analysis = process_zip_file(file_data)
            if 'error' in zip_analysis:
                analysis += f"Error: {zip_analysis['error']}\n"
            else:
                analysis += f"Archive contains {zip_analysis['file_count']} files\n"
                analysis += f"Total extracted size: {format_file_size(zip_analysis['total_size'])}\n\n"
                analysis += "📋 **Contents:**\n"
                
                for file_info in zip_analysis['file_summary']:
                    analysis += f"- {file_info['path']} ({format_file_size(file_info['size'])}) [{file_info['type']}]\n"
                
                # Include content of text files
                text_files = {k: v for k, v in zip_analysis['file_contents'].items() if v['type'] == 'text'}
                if text_files:
                    analysis += "\n📝 **Text File Contents:**\n"
                    for file_path, file_info in text_files.items():
                        analysis += f"\n--- {file_path} ---\n"
                        # Limit content length to avoid overwhelming the model
                        content = file_info['content']
                        if len(content) > 2000:
                            content = content[:2000] + "\n... (truncated)"
                        analysis += content + "\n"
        
        # Handle image files
        elif file_data['type'].startswith('image/'):
            analysis += "📷 **Image Analysis Required**\n"
            analysis += "I've received an image file. Please analyze this image and provide insights about:\n"
            analysis += "- Visual content and elements\n"
            analysis += "- Any text present (OCR)\n"
            analysis += "- Suggestions for UI/UX improvements if applicable\n"
            analysis += "- Technical observations about the image\n"
        
        # Handle video files
        elif file_data['type'].startswith('video/'):
            analysis += "🎬 **Video Analysis Required**\n"
            analysis += "I've received a video file. Please analyze this video content and provide:\n"
            analysis += "- Description of visual content\n"
            analysis += "- Key scenes or moments\n"
            analysis += "- Testing recommendations if this is a screen recording\n"
            analysis += "- Technical observations about the video\n"
        
        # Handle audio files
        elif file_data['type'].startswith('audio/'):
            analysis += "🎵 **Audio Analysis Required**\n"
            analysis += "I've received an audio file. Please analyze this audio content and provide:\n"
            analysis += "- Transcription if speech is present\n"
            analysis += "- Audio quality assessment\n"
            analysis += "- Content summary and insights\n"
        
        # Handle other document types
        elif file_data['type'] in ['application/pdf', 'text/plain', 'application/msword']:
            analysis += "📄 **Document Analysis Required**\n"
            analysis += "I've received a document file. Please analyze the content and provide:\n"
            analysis += "- Content summary and key points\n"
            analysis += "- Insights and recommendations\n"
            analysis += "- Any improvements or suggestions\n"
        
        file_analysis.append(analysis)
    
    # Combine original message with file analysis
    enhanced_message = message
    if file_analysis:
        enhanced_message += "\n\n" + "".join(file_analysis)
        enhanced_message += "\n\n**Please analyze the uploaded files and provide relevant insights, testing advice, or assistance based on their content.**"
    
    logger.info(f"Enhanced message length: {len(enhanced_message)} characters")
    return enhanced_message

def format_file_size(bytes_size):
    """Format file size in human readable format"""
    if bytes_size == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB"]
    i = 0
    while bytes_size >= 1024 and i < len(size_names) - 1:
        bytes_size /= 1024.0
        i += 1
    
    return f"{bytes_size:.1f} {size_names[i]}"

@app.route('/api/chat', methods=['POST'])
def chat():
    """Enhanced chat endpoint with proper Grazie API file attachment support via LLMChatMediaMessage"""
    try:
        data = request.get_json()
        token = data.get('token')
        environment = data.get('environment', 'staging')
        model = data.get('model')
        message = data.get('message')
        system_message = data.get('system_message', '')
        stream = data.get('stream', True)
        parameters = data.get('parameters', {})
        files = data.get('files', [])
        
        # Enhanced logging
        model_id_header = request.headers.get('X-Model-ID', 'unknown')
        logger.info(f"=== CHAT REQUEST START ===")
        logger.info(f"Model: {model} (Header: {model_id_header})")
        logger.info(f"Environment: {environment}")
        logger.info(f"Message length: {len(message)} chars")
        logger.info(f"Files attached: {len(files)}")
        logger.info(f"Stream enabled: {stream}")
        logger.info(f"Parameters: {parameters}")
        
        if files:
            for i, file_data in enumerate(files):
                logger.info(f"  File {i+1}: {file_data.get('name', 'unknown')} ({file_data.get('type', 'unknown')}, {file_data.get('size', 0)} bytes)")
        
        if not all([token, model, message]):
            logger.error("Missing required parameters")
            return jsonify({'error': 'Token, model, and message are required'}), 400
        
        try:
            client = GrazieClient(jwt_token=token, environment=environment)
        except Exception as e:
            logger.error(f"Failed to create Grazie client: {e}")
            return jsonify({'error': f'Failed to initialize client: {str(e)}'}), 500
        
        if not client.validate_model_for_chat(model):
            logger.error(f"Model {model} does not support chat")
            return jsonify({'error': f'Model {model} does not support chat'}), 400
        
        # Build messages array with proper format for files
        messages = []
        
        # Add system message if provided
        if system_message:
            messages.append({
                "type": "system_message",
                "content": system_message
            })
        
        # Add user message
        messages.append({
            "type": "user_message", 
            "content": message
        })
        
        # Check if model supports media/vision before adding file attachments
        model_supports_media = False
        try:
            capabilities = client.get_model_capabilities(model)
            features = capabilities.get('features', [])
            
            # Debug: Log all capabilities
            logger.info(f"Model {model} capabilities: {capabilities}")
            logger.info(f"Model {model} features: {features}")
            
            # Check for vision support - try different possible feature names
            vision_indicators = ['Vision', 'vision', 'Multimodal', 'multimodal', 'Image', 'image']
            model_supports_media = any(indicator in str(features) for indicator in vision_indicators)
            
            # Also check if it's a known vision model
            known_vision_models = [
                'anthropic-claude', 'claude', 'gemini', 'gpt-4-vision', 'gpt-4o', 'gpt-4-turbo'
            ]
            if any(known_model in model.lower() for known_model in known_vision_models):
                model_supports_media = True
                logger.info(f"Model {model} identified as known vision model")
            
            logger.info(f"Model {model} supports media: {model_supports_media}")
            
        except Exception as e:
            logger.warning(f"Could not check capabilities for {model}: {e}")
            # Default to True for known vision models if capability check fails
            known_vision_models = [
                'anthropic-claude', 'claude', 'gemini', 'gpt-4-vision', 'gpt-4o', 'gpt-4-turbo'
            ]
            if any(known_model in model.lower() for known_model in known_vision_models):
                model_supports_media = True
                logger.info(f"Defaulting to vision support for known model: {model}")
        
        # Add file attachments only for models that support media
        if files:
            if model_supports_media:
                logger.info("Converting files to media message format for vision-capable model")
                for file_data in files:
                    # Only send image files for now (most common media type)
                    if file_data.get("type", "").startswith("image/"):
                        media_message = {
                            "type": "media_message",
                            "mediaType": file_data.get("type", "image/png"),
                            "data": file_data.get("content", "")  # Base64 content
                        }
                        messages.append(media_message)
                        logger.info(f"Added media message: {file_data.get('name')} ({media_message['mediaType']})")
                    else:
                        logger.info(f"Skipping non-image file for media model: {file_data.get('name')} ({file_data.get('type')})")
            else:
                logger.warning(f"Model {model} does not support media - skipping {len(files)} file(s)")
                # Enhance the user message with file descriptions instead
                file_descriptions = []
                for file_data in files:
                    file_descriptions.append(f"- {file_data.get('name')} ({file_data.get('type')}, {format_file_size(file_data.get('size', 0))})")
                
                if file_descriptions:
                    enhanced_message = message + "\n\n**Note: Files were attached but this model doesn't support media analysis:**\n" + "\n".join(file_descriptions)
                    # Update the user message
                    messages[-1]["content"] = enhanced_message
        
        logger.info(f"Final messages array: {len(messages)} messages")
        for i, msg in enumerate(messages):
            logger.info(f"  Message {i+1}: {msg.get('type')} - {len(str(msg.get('content', msg.get('data', ''))))} chars")
        
        if stream:
            def generate():
                try:
                    logger.info(f"Starting streaming response for model: {model}")
                    
                    chunk_count = 0
                    # Use standard chat_stream with messages containing media messages
                    for chunk in client.chat_stream(messages, model, parameters):
                        chunk_count += 1
                        if chunk.get("type") == "Content":
                            yield f"data: {json.dumps({'content': chunk.get('content', '')})}\n\n"
                        elif chunk.get("type") == "FinishMetadata":
                            logger.info(f"Stream finished for {model} after {chunk_count} chunks")
                            yield f"data: {json.dumps({'finish_reason': chunk.get('reason')})}\n\n"
                        elif chunk.get("type") == "QuotaMetadata":
                            yield f"data: {json.dumps({'quota': chunk})}\n\n"
                    
                    yield f"data: {json.dumps({'done': True})}\n\n"
                
                except Exception as e:
                    logger.error(f"Streaming error for model {model}: {str(e)}\n{traceback.format_exc()}")
                    yield f"data: {json.dumps({'error': str(e)})}\n\n"
            
            logger.info(f"Returning streaming response for model: {model}")
            return Response(generate(), mimetype='text/plain', headers={
                'Cache-Control': 'no-cache',
                'Connection': 'keep-alive',
                'Access-Control-Allow-Origin': '*'
            })
        else:
            # Non-streaming response
            try:
                logger.info(f"Starting non-streaming response for model: {model}")
                
                # Use chat_complete with messages containing media messages
                content_parts = []
                for chunk in client.chat_stream(messages, model, parameters):
                    if chunk.get("type") == "Content":
                        content_parts.append(chunk.get("content", ""))
                
                response = "".join(content_parts)
                logger.info(f"Non-streaming response completed for model: {model}")
                return jsonify({'response': response})
            except Exception as e:
                logger.error(f"Non-streaming error for model {model}: {str(e)}\n{traceback.format_exc()}")
                return jsonify({'error': str(e)}), 500
    
    except Exception as e:
        logger.error(f"Chat endpoint error: {str(e)}\n{traceback.format_exc()}")
        return jsonify({'error': str(e)}), 500
    finally:
        logger.info(f"=== CHAT REQUEST END ===")

@app.route('/api/analyze_files', methods=['POST'])
def analyze_files():
    """Dedicated endpoint for file analysis"""
    try:
        data = request.get_json()
        files = data.get('files', [])
        
        logger.info(f"Analyzing {len(files)} files")
        
        if not files:
            return jsonify({'error': 'No files provided'}), 400
        
        analysis_results = []
        
        for file_data in files:
            result = {
                'name': file_data['name'],
                'type': file_data['type'],
                'size': file_data.get('size', 0)
            }
            
            # Handle ZIP files
            if file_data['name'].lower().endswith('.zip'):
                zip_analysis = process_zip_file(file_data)
                result['analysis'] = zip_analysis
            else:
                # Check if file type is supported
                supported_types = ['image/', 'video/', 'audio/', 'text/', 'application/pdf']
                is_supported = any(file_data['type'].startswith(t) for t in supported_types)
                
                result['analysis'] = {
                    'supported': is_supported,
                    'file_type': 'multimedia' if file_data['type'].startswith(('image/', 'video/', 'audio/')) else 'document'
                }
            
            analysis_results.append(result)
        
        return jsonify({'files': analysis_results})
    
    except Exception as e:
        logger.error(f"File analysis error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/validate_token', methods=['POST'])
def validate_token():
    """Validate JWT token for the specified environment"""
    try:
        data = request.get_json()
        token = data.get('token')
        environment = data.get('environment', 'staging')
        
        logger.info(f"Validating token for environment: {environment}")
        
        if not token:
            return jsonify({'valid': False, 'error': 'Token is required'}), 400
        
        try:
            client = GrazieClient(jwt_token=token, environment=environment)
            logger.info("Token validation successful")
            return jsonify({'valid': True, 'chat_available': client.is_chat_available()})
        except ValueError as e:
            logger.warning(f"Token validation failed: {e}")
            return jsonify({'valid': False, 'error': str(e)})
    
    except Exception as e:
        logger.error(f"Token validation error: {str(e)}")
        return jsonify({'valid': False, 'error': str(e)})

@app.errorhandler(413)
def too_large(e):
    logger.warning("File upload too large")
    return jsonify({'error': 'File too large. Maximum size is 100MB.'}), 413

@app.errorhandler(Exception)
def handle_exception(e):
    logger.error(f"Unhandled exception: {str(e)}\n{traceback.format_exc()}")
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    # Enable debug logging
    app.run(debug=True, host='0.0.0.0', port=8000) 