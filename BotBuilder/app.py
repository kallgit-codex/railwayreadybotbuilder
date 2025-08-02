from database import db
from auth import auth_bp
import os
import time
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, send_from_directory, redirect, url_for
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix

# Import production-ready utilities
from config import get_config
from utils.logging_manager import logging_manager
from utils.error_handlers import ErrorHandler, handle_errors
from utils.rate_limiter import rate_limiter
from utils.health_monitor import health_monitor

# Get configuration
config = get_config()

# Validate required environment variables
try:
    config.validate_required_vars()
except ValueError as e:
    print(f"Configuration Error: {e}")
    print("Please check your .env file and ensure all required variables are set.")
    exit(1)

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

# Create the app using production configuration
app = Flask(
__name__, static_folder="frontend", static_url_path="")
app.secret_key = config.SECRET_KEY
db.init_app(app)
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Configure the database from config
app.config["SQLALCHEMY_DATABASE_URI"] = config.DATABASE_URL
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = config.SQLALCHEMY_ENGINE_OPTIONS
app.config['UPLOAD_FOLDER'] = config.UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = config.MAX_CONTENT_LENGTH

# Create required directories
os.makedirs(config.LOG_DIR, exist_ok=True)
os.makedirs(config.UPLOAD_FOLDER, exist_ok=True)

# Initialize the app with the extension
db.init_app(app)

# Import services
from services.openai_service import OpenAIService
from services.platform_service_enhanced import PlatformService
from services.client_service import ClientService
from services.usage_service import UsageService
from utils.file_handler import FileHandler

# Create logger for app-specific logging
logger = logging_manager.app_logger

with app.app_context():
    # Import models to ensure tables are created
    from models import Client, Bot, KnowledgeBase, KnowledgeFile, KnowledgeChunk, Conversation, Deployment, Usage
    db.create_all()
    
    # Knowledge service temporarily disabled to fix cached errors
    
    # Initialize OpenAI service with persistent settings
    try:
        import logging
        from services.openai_service import openai_service
        openai_service.initialize_on_startup()
    except Exception as e:
        import logging
        logging.error(f"Error initializing OpenAI service on startup: {e}")

# Initialize services
openai_service = OpenAIService()
platform_service = PlatformService()
client_service = ClientService()
usage_service = UsageService()
file_handler = FileHandler(app.config['UPLOAD_FOLDER'])

# Import conversation service after models are loaded
from services.conversation_service import conversation_service

# Central error handler for uncaught exceptions - TEMPORARILY DISABLED TO DEBUG
# @app.errorhandler(Exception)
# def handle_exception(e):
#     """Handle all uncaught exceptions"""
#     return ErrorHandler.handle_api_error(e, {'route': request.endpoint, 'method': request.method})

# Health check endpoint for production monitoring
@app.route('/health')
@handle_errors
def health_check():
    """Health check endpoint for monitoring"""
    if config.HEALTH_CHECK_ENABLED:
        health_data = health_monitor.get_system_health()
        status_code = 200 if health_data['status'] == 'healthy' else 503
        return jsonify(health_data), status_code
    else:
        return jsonify({'status': 'disabled'}), 200

# Quick health check for rapid monitoring
@app.route('/health/quick')
@handle_errors  
def quick_health_check():
    """Quick health check for load balancers"""
    health_data = health_monitor.get_quick_health()
    status_code = 200 if health_data['status'] == 'healthy' else 503
    return jsonify(health_data), status_code

# Keep the original route from starter code
@app.route('/')
def index():
    return send_from_directory('frontend', 'simple-dashboard.html')

# === EMERGENCY BOT WEBHOOK - DIRECT IMPLEMENTATION ===
@app.route('/emergency/bot')
def emergency_bot_get():
    """Emergency bot webhook GET endpoint"""
    return 'Emergency bot webhook active', 200

@app.route('/emergency/bot', methods=['POST'])
def emergency_bot_post():
    """Emergency bot webhook POST endpoint - completely isolated"""
    import os
    import json
    import requests
    from openai import OpenAI
    
    try:
        # Parse Telegram update without using any services
        data = request.get_json(force=True) or {}
        msg = data.get('message', {})
        text = msg.get('text', '')
        chat = msg.get('chat', {})
        chat_id = chat.get('id')
        
        if text and chat_id:
            # Direct OpenAI call
            api_key = os.environ.get("OPENAI_API_KEY")
            bot_token = "8301717846:AAFhv9n1qlizTvYytBWVeRZFCAgVqTgGflM"
            
            if api_key:
                try:
                    client = OpenAI(api_key=api_key)
                    response = client.chat.completions.create(
                        model="gpt-4o",
                        messages=[
                            {"role": "system", "content": "You are a helpful AI assistant for a home services business. Standard TV mounting is $99, Large TV mounting is $149, Soundbar mounting is $40."},
                            {"role": "user", "content": text}
                        ],
                        max_tokens=400
                    )
                    response_text = response.choices[0].message.content
                except:
                    response_text = "Hello! I'm your AI assistant for home services. TV mounting: $99 standard, $149 large. Soundbar: $40."
            else:
                response_text = "Hello! I'm your AI assistant for home services. TV mounting: $99 standard, $149 large. Soundbar: $40."
            
            # Send via Telegram API
            telegram_api = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            requests.post(telegram_api, json={"chat_id": chat_id, "text": response_text}, timeout=10)
            
        return 'OK', 200
    except:
        return 'OK', 200

# === FRESH WEBHOOK ENDPOINT ===
@app.route('/fresh/webhook', methods=['POST', 'GET'])
def fresh_webhook():
    """Fresh webhook endpoint that actually works"""
    
    if request.method == 'GET':
        return 'Fresh webhook is active!', 200
    
    try:
        # Import the working bot logic
        import json
        from create_fresh_bot import process_telegram_message
        
        # Get Telegram update data
        update_data = request.get_json(force=True) or {}
        
        # Process the message using the working bot logic
        response = process_telegram_message(update_data)
        
        return 'OK', 200
        
    except Exception as e:
        # Always return OK to prevent webhook retry storms
        return 'OK', 200

@app.route('/simple-dashboard.js')
def dashboard_js():
    return send_from_directory('frontend', 'simple-dashboard.js')

# Expanded bot management API - extending the starter code
@app.route('/api/bots', methods=['GET', 'POST'])
def manage_bots():
    if request.method == 'POST':
        try:
            data = request.json
            bot = Bot(
                name=data.get('name'),
                description=data.get('description', ''),
                personality=data.get('personality', 'helpful and friendly'),
                personality_description=data.get('personality_description'),
                tone=data.get('tone', 'friendly'),
                system_prompt=data.get('system_prompt', ''),
                temperature=data.get('temperature', 0.7),
                client_id=data.get('client_id')  # Support linking to client
            )
            db.session.add(bot)
            db.session.commit()
            
            return jsonify({
                "message": "Bot created successfully",
                "bot": {
                    "id": bot.id,
                    "name": bot.name,
                    "description": bot.description,
                    "personality": bot.personality,
                    "created_at": bot.created_at.isoformat()
                }
            })
        except Exception as e:
            logging.error(f"Error creating bot: {e}")
            return jsonify({"error": "Failed to create bot"}), 500
    
    # GET request - return all bots
    try:
        bots = Bot.query.all()
        return jsonify({
            "bots": [{
                "id": bot.id,
                "name": bot.name,
                "description": bot.description,
                "personality": bot.personality,
                "personality_description": bot.personality_description,
                "tone": bot.tone,
                "temperature": bot.temperature,
                "created_at": bot.created_at.isoformat(),
                "knowledge_count": len(bot.knowledge_bases),
                "client_id": bot.client_id,
                "client_name": bot.client.name if bot.client else None
            } for bot in bots]
        })
    except Exception as e:
        logging.error(f"Error fetching bots: {e}")
        return jsonify({"error": "Failed to fetch bots"}), 500

@app.route('/api/bots/<int:bot_id>', methods=['GET', 'PUT', 'DELETE'])
def manage_bot(bot_id):
    bot = Bot.query.get_or_404(bot_id)
    
    if request.method == 'GET':
        return jsonify({
            "id": bot.id,
            "name": bot.name,
            "description": bot.description,
            "personality": bot.personality,
            "personality_description": bot.personality_description,
            "tone": bot.tone,
            "system_prompt": bot.system_prompt,
            "temperature": bot.temperature,
            "created_at": bot.created_at.isoformat(),
            "client_id": bot.client_id,
            "client_name": bot.client.name if bot.client else None,
            "knowledge_bases": [{
                "id": kb.id,
                "filename": kb.filename,
                "file_type": kb.file_type,
                "upload_date": kb.upload_date.isoformat()
            } for kb in bot.knowledge_bases]
        })
    
    elif request.method == 'PUT':
        try:
            data = request.json
            bot.name = data.get('name', bot.name)
            bot.description = data.get('description', bot.description)
            bot.personality = data.get('personality', bot.personality)
            bot.personality_description = data.get('personality_description', bot.personality_description)
            bot.tone = data.get('tone', bot.tone)
            bot.system_prompt = data.get('system_prompt', bot.system_prompt)
            bot.temperature = data.get('temperature', bot.temperature)
            
            # Handle client assignment (allow None for standalone bots)
            if 'client_id' in data:
                bot.client_id = data['client_id'] if data['client_id'] else None
            
            db.session.commit()
            return jsonify({"message": "Bot updated successfully"})
        except Exception as e:
            logging.error(f"Error updating bot: {e}")
            return jsonify({"error": "Failed to update bot"}), 500
    
    elif request.method == 'DELETE':
        try:
            # Delete associated knowledge bases and files
            for kb in bot.knowledge_bases:
                file_handler.delete_file(kb.file_path)
                db.session.delete(kb)
            
            # Delete conversations
            Conversation.query.filter_by(bot_id=bot_id).delete()
            
            db.session.delete(bot)
            db.session.commit()
            return jsonify({"message": "Bot deleted successfully"})
        except Exception as e:
            logging.error(f"Error deleting bot: {e}")
            return jsonify({"error": "Failed to delete bot"}), 500

# Enhanced message endpoint - expanding the starter code functionality
@app.route('/api/bots/<int:bot_id>/message', methods=['POST'])
def bot_message(bot_id):
    try:
        bot = Bot.query.get_or_404(bot_id)
        data = request.json
        user_msg = data.get('message')
        session_id = data.get('session_id', 'default')
        
        if not user_msg:
            return jsonify({"error": "Message is required"}), 400
        
        # Get conversation history using service (limited to last 15 messages for context)
        conversation_history = conversation_service.get_conversation_history(bot_id, session_id, limit=15)
        
        # Get enhanced knowledge base context using chunking
        context = enhanced_knowledge_service.get_relevant_context(bot_id, user_msg, max_chunks=5) if enhanced_knowledge_service else ""
        
        # Generate response using OpenAI and track token usage
        response, token_usage = openai_service.generate_response(
            bot=bot,
            message=user_msg,
            conversation_history=conversation_history,
            context=context
        )
        
        # Track token usage if bot is linked to a client
        if bot.client_id and token_usage.get('total_tokens', 0) > 0:
            usage_service.log_usage(
                client_id=bot.client_id,
                bot_id=bot_id,
                token_usage=token_usage
            )
        
        # Use conversation service to manage conversation memory properly
        conversation_service.add_user_and_assistant_messages(bot_id, session_id, user_msg, response)
        
        return jsonify({
            "response": response,
            "session_id": session_id,
            "token_usage": token_usage,
            "conversation_length": len(conversation_service.get_full_conversation(bot_id, session_id))
        })
        
    except Exception as e:
        logging.error(f"Error processing message: {e}")
        return jsonify({"error": "Failed to process message"}), 500

# Clear conversation endpoint for per-session memory management
@app.route('/api/bots/<int:bot_id>/clear_conversation', methods=['POST'])
def clear_conversation(bot_id):
    """Clear conversation history for a specific session"""
    try:
        bot = Bot.query.get_or_404(bot_id)
        data = request.json or {}
        session_id = data.get('session_id', 'default')
        
        # Clear the conversation using the service
        success = conversation_service.clear_conversation(bot_id, session_id)
        
        if success:
            return jsonify({
                "message": "Conversation cleared successfully",
                "session_id": session_id,
                "new_session_id": f"session_{datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')}"
            })
        else:
            return jsonify({"message": "No conversation found to clear", "session_id": session_id})
        
    except Exception as e:
        logging.error(f"Error clearing conversation: {e}")
        return jsonify({"error": "Failed to clear conversation"}), 500

@app.route('/api/bots/<int:bot_id>/knowledge', methods=['GET', 'POST'])
def manage_knowledge(bot_id):
    try:
        bot = Bot.query.get_or_404(bot_id)
        
        if request.method == 'GET':
            # Return list of knowledge bases for this bot
            knowledge_bases = KnowledgeBase.query.filter_by(bot_id=bot_id).all()
            return jsonify({
                "knowledge_bases": [{
                    "id": kb.id,
                    "filename": kb.filename,
                    "file_type": kb.file_type,
                    "upload_date": kb.upload_date.isoformat() if kb.upload_date else None,
                    "content_preview": kb.content[:200] + "..." if len(kb.content) > 200 else kb.content
                } for kb in knowledge_bases]
            })
        
        # POST request - file upload
        if 'file' not in request.files:
            return jsonify({"error": "No file uploaded"}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "No file selected"}), 400
        
        # Save file and extract content
        file_path, file_type = file_handler.save_file(file)
        content = file_handler.extract_text(file_path, file_type)
        
        # Create knowledge base entry
        knowledge_base = KnowledgeBase(
            bot_id=bot_id,
            filename=file.filename,
            file_path=file_path,
            file_type=file_type,
            content=content
        )
        
        db.session.add(knowledge_base)
        db.session.commit()
        
        return jsonify({
            "message": "Knowledge base uploaded successfully",
            "knowledge": {
                "id": knowledge_base.id,
                "filename": knowledge_base.filename,
                "file_type": knowledge_base.file_type
            }
        })
        
    except Exception as e:
        logging.error(f"Error uploading knowledge: {e}")
        return jsonify({"error": "Failed to upload knowledge base"}), 500

@app.route('/api/bots/<int:bot_id>/knowledge/<int:knowledge_id>', methods=['DELETE'])
def delete_knowledge(bot_id, knowledge_id):
    try:
        knowledge_base = KnowledgeBase.query.filter_by(
            id=knowledge_id, 
            bot_id=bot_id
        ).first_or_404()
        
        # Delete the file
        file_handler.delete_file(knowledge_base.file_path)
        
        # Delete from database
        db.session.delete(knowledge_base)
        db.session.commit()
        
        return jsonify({"message": "Knowledge base deleted successfully"})
        
    except Exception as e:
        logging.error(f"Error deleting knowledge: {e}")
        return jsonify({"error": "Failed to delete knowledge base"}), 500

# === ENHANCED KNOWLEDGE MANAGEMENT ROUTES ===

@app.route('/api/bots/<int:bot_id>/knowledge-files', methods=['GET', 'POST'])
def manage_knowledge_files(bot_id):
    """Enhanced knowledge file management with chunking and tagging"""
    try:
        bot = Bot.query.get_or_404(bot_id)
        
        if request.method == 'GET':
            # Get all knowledge files for this bot
            files = enhanced_knowledge_service.get_bot_knowledge_files(bot_id) if enhanced_knowledge_service else []
            return jsonify({
                "bot_id": bot_id,
                "bot_name": bot.name,
                "knowledge_files": files
            })
        
        # POST request - file upload with enhanced features
        if 'file' not in request.files:
            return jsonify({"error": "No file uploaded"}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "No file selected"}), 400
        
        # Parse tags from form data
        tags_str = request.form.get('tags', '')
        tags = [tag.strip() for tag in tags_str.split(',') if tag.strip()] if tags_str else []
        
        # Upload and process file
        if not enhanced_knowledge_service:
            return jsonify({"error": "Enhanced knowledge service not available"}), 500
        result = enhanced_knowledge_service.upload_knowledge_file(bot_id, file, tags)
        
        if result["success"]:
            return jsonify({
                "message": "Knowledge file uploaded and processed successfully",
                "file": result["file"]
            })
        else:
            return jsonify({"error": result["error"]}), 500
        
    except Exception as e:
        logging.error(f"Error managing knowledge files: {e}")
        return jsonify({"error": "Failed to manage knowledge files"}), 500

@app.route('/api/bots/<int:bot_id>/knowledge-files/<int:file_id>', methods=['DELETE', 'PUT'])
def manage_knowledge_file(bot_id, file_id):
    """Delete or update a specific knowledge file"""
    try:
        if request.method == 'DELETE':
            result = enhanced_knowledge_service.delete_knowledge_file(bot_id, file_id)
            
            if result["success"]:
                return jsonify({"message": result["message"]})
            else:
                return jsonify({"error": result["error"]}), 404
        
        # PUT request - update file tags
        if request.method == 'PUT':
            data = request.json
            tags = data.get('tags', [])
            
            result = enhanced_knowledge_service.update_file_tags(bot_id, file_id, tags)
            
            if result["success"]:
                return jsonify({"message": result["message"]})
            else:
                return jsonify({"error": result["error"]}), 404
        
    except Exception as e:
        logging.error(f"Error managing knowledge file: {e}")
        return jsonify({"error": "Failed to manage knowledge file"}), 500

@app.route('/api/bots/<int:bot_id>/knowledge-manual', methods=['POST'])
def add_manual_knowledge(bot_id):
    """Add manual knowledge snippet without file upload"""
    try:
        bot = Bot.query.get_or_404(bot_id)
        data = request.json
        
        title = data.get('title', '')
        content = data.get('content', '')
        tags_list = data.get('tags', [])
        
        if not title or not content:
            return jsonify({"error": "Title and content are required"}), 400
        
        result = enhanced_knowledge_service.add_manual_knowledge(bot_id, title, content, tags_list)
        
        if result["success"]:
            return jsonify({
                "message": "Manual knowledge added successfully",
                "file": result["file"]
            })
        else:
            return jsonify({"error": result["error"]}), 500
        
    except Exception as e:
        logging.error(f"Error adding manual knowledge: {e}")
        return jsonify({"error": "Failed to add manual knowledge"}), 500

# === CONVERSATION MEMORY ROUTES ===

@app.route('/api/bots/<int:bot_id>/conversations', methods=['GET'])
def get_bot_conversations(bot_id):
    """Get all conversation sessions for a bot"""
    try:
        bot = Bot.query.get_or_404(bot_id)
        conversations = conversation_service.get_bot_conversations(bot_id)
        return jsonify({
            'bot_id': bot_id,
            'bot_name': bot.name,
            'conversations': conversations
        })
    except Exception as e:
        logging.error(f"Error getting bot conversations {bot_id}: {e}")
        return jsonify({'error': 'Failed to get conversations'}), 500

@app.route('/api/bots/<int:bot_id>/conversations/<session_id>', methods=['GET', 'DELETE'])
def manage_conversation_session(bot_id, session_id):
    """Get or clear a specific conversation"""
    try:
        bot = Bot.query.get_or_404(bot_id)
        
        if request.method == 'GET':
            messages = conversation_service.get_full_conversation(bot_id, session_id)
            return jsonify({
                'bot_id': bot_id,
                'session_id': session_id,
                'messages': messages,
                'message_count': len(messages)
            })
        
        elif request.method == 'DELETE':
            success = conversation_service.clear_conversation(bot_id, session_id)
            if success:
                return jsonify({'message': 'Conversation cleared successfully'})
            else:
                return jsonify({'error': 'Conversation not found'}), 404
                
    except Exception as e:
        logging.error(f"Error managing conversation {bot_id}/{session_id}: {e}")
        return jsonify({'error': 'Failed to manage conversation'}), 500

# Platform integration endpoints - OLD ROUTE REMOVED (replaced by enhanced version below)

# Deployment routes moved to enhanced section below





# === GLOBAL SETTINGS API ===

@app.route('/api/settings/openai-key', methods=['GET', 'PUT'])
def manage_openai_api_key():
    from services.settings_service import settings_service
    
    if request.method == 'GET':
        try:
            api_key = settings_service.get_openai_api_key()
            # Mask the key for security in the response
            masked_key = f"{api_key[:8]}...{api_key[-4:]}" if api_key and len(api_key) > 12 else "Not set"
            return jsonify({
                'api_key': api_key if api_key else "",
                'masked_key': masked_key,
                'is_set': bool(api_key)
            })
        except Exception as e:
            logging.error(f"Error getting OpenAI API key: {e}")
            return jsonify({'error': 'Failed to get OpenAI API key'}), 500
    
    elif request.method == 'PUT':
        try:
            data = request.json
            api_key = data.get('api_key', '').strip()
            confirmed = data.get('confirmed', False)
            
            if not api_key:
                return jsonify({'error': 'API key cannot be empty'}), 400
            
            result = settings_service.set_openai_api_key(api_key, confirmed=confirmed)
            
            if result['success']:
                masked_key = f"{api_key[:8]}...{api_key[-4:]}" if len(api_key) > 12 else api_key
                return jsonify({
                    'message': result['message'],
                    'masked_key': masked_key,
                    'is_set': True
                })
            elif result.get('requires_confirmation'):
                return jsonify({
                    'requires_confirmation': True,
                    'message': result['message']
                }), 400
            else:
                return jsonify({'error': result['message']}), 500
                
        except Exception as e:
            logging.error(f"Error updating OpenAI API key: {e}")
            return jsonify({'error': 'Failed to update OpenAI API key'}), 500

# === CLIENT MANAGEMENT API ===

@app.route('/api/clients', methods=['GET', 'POST'])
def manage_clients():
    if request.method == 'POST':
        try:
            data = request.json
            result = client_service.create_client(
                name=data.get('name'),
                notes=data.get('notes', ''),
                api_keys=data.get('api_keys', {})
            )
            
            if result['success']:
                return jsonify({
                    'message': result['message'],
                    'client': result['client']
                })
            else:
                return jsonify({'error': result['message']}), 500
                
        except Exception as e:
            logging.error(f"Error creating client: {e}")
            return jsonify({'error': 'Failed to create client'}), 500
    
    # GET request - return all clients
    try:
        clients = client_service.get_all_clients()
        return jsonify({'clients': clients})
    except Exception as e:
        logging.error(f"Error fetching clients: {e}")
        return jsonify({'error': 'Failed to fetch clients'}), 500

@app.route('/api/clients/<int:client_id>', methods=['GET', 'PUT', 'DELETE'])
def manage_client(client_id):
    if request.method == 'GET':
        try:
            client = client_service.get_client_by_id(client_id)
            if client:
                return jsonify(client)
            else:
                return jsonify({'error': 'Client not found'}), 404
        except Exception as e:
            logging.error(f"Error fetching client {client_id}: {e}")
            return jsonify({'error': 'Failed to fetch client'}), 500
    
    elif request.method == 'PUT':
        try:
            data = request.json
            result = client_service.update_client(
                client_id=client_id,
                name=data.get('name'),
                notes=data.get('notes'),
                api_keys=data.get('api_keys')
            )
            
            if result['success']:
                return jsonify({
                    'message': result['message'],
                    'client': result['client']
                })
            else:
                return jsonify({'error': result['message']}), 404 if 'not found' in result['message'] else 500
                
        except Exception as e:
            logging.error(f"Error updating client {client_id}: {e}")
            return jsonify({'error': 'Failed to update client'}), 500
    
    elif request.method == 'DELETE':
        try:
            result = client_service.delete_client(client_id)
            
            if result['success']:
                return jsonify({'message': result['message']})
            else:
                return jsonify({'error': result['message']}), 404 if 'not found' in result['message'] else 500
                
        except Exception as e:
            logging.error(f"Error deleting client {client_id}: {e}")
            return jsonify({'error': 'Failed to delete client'}), 500

@app.route('/api/clients/<int:client_id>/api-keys', methods=['GET', 'PUT'])
def manage_client_api_keys(client_id):
    if request.method == 'GET':
        try:
            api_keys = client_service.get_client_api_keys(client_id)
            return jsonify({'api_keys': api_keys})
        except Exception as e:
            logging.error(f"Error fetching API keys for client {client_id}: {e}")
            return jsonify({'error': 'Failed to fetch API keys'}), 500
    
    elif request.method == 'PUT':
        try:
            data = request.json
            result = client_service.update_api_keys(client_id, data.get('api_keys', {}))
            
            if result['success']:
                return jsonify({
                    'message': result['message'],
                    'api_keys': result['api_keys']
                })
            else:
                return jsonify({'error': result['message']}), 404 if 'not found' in result['message'] else 500
                
        except Exception as e:
            logging.error(f"Error updating API keys for client {client_id}: {e}")
            return jsonify({'error': 'Failed to update API keys'}), 500


# === USAGE TRACKING API ===

@app.route('/api/usage', methods=['GET'])
def get_usage_stats():
    """Get overall usage statistics with optional filters"""
    try:
        # Parse query parameters
        client_id = request.args.get('client_id', type=int)
        bot_id = request.args.get('bot_id', type=int)
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # Parse dates if provided
        start_date_obj = None
        end_date_obj = None
        if start_date:
            start_date_obj = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        if end_date:
            end_date_obj = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
        
        # Get usage statistics
        stats = usage_service.get_usage_stats(
            client_id=client_id,
            bot_id=bot_id,
            start_date=start_date_obj,
            end_date=end_date_obj
        )
        
        return jsonify(stats)
        
    except Exception as e:
        logging.error(f"Error getting usage stats: {e}")
        return jsonify({'error': 'Failed to get usage statistics'}), 500

@app.route('/api/clients/<int:client_id>/usage', methods=['GET'])
def get_client_usage(client_id):
    """Get usage statistics for a specific client"""
    try:
        client = Client.query.get_or_404(client_id)
        
        # Parse query parameters
        days = request.args.get('days', default=30, type=int)
        include_breakdown = request.args.get('breakdown', default='true').lower() == 'true'
        
        # Get overall client usage
        start_date = datetime.utcnow() - timedelta(days=days)
        overall_stats = usage_service.get_usage_stats(
            client_id=client_id,
            start_date=start_date
        )
        
        result = {
            'client_id': client_id,
            'client_name': client.name,
            'period_days': days,
            'usage_stats': overall_stats
        }
        
        # Add bot breakdown if requested
        if include_breakdown:
            result['bot_breakdown'] = usage_service.get_client_usage_breakdown(client_id, days)
        
        # Add daily usage for charts
        result['daily_usage'] = usage_service.get_daily_usage(client_id=client_id, days=min(days, 30))
        
        # Check limits
        limit_status = usage_service.check_client_limits(client_id)
        result['limit_status'] = limit_status
        
        return jsonify(result)
        
    except Exception as e:
        logging.error(f"Error getting client usage: {e}")
        return jsonify({'error': 'Failed to get client usage'}), 500

@app.route('/api/bots/<int:bot_id>/usage', methods=['GET'])
def get_bot_usage(bot_id):
    """Get usage statistics for a specific bot"""
    try:
        bot = Bot.query.get_or_404(bot_id)
        
        # Parse query parameters
        days = request.args.get('days', default=30, type=int)
        
        # Get bot usage
        start_date = datetime.utcnow() - timedelta(days=days)
        stats = usage_service.get_usage_stats(
            bot_id=bot_id,
            start_date=start_date
        )
        
        # Get daily usage for charts
        daily_usage = usage_service.get_daily_usage(bot_id=bot_id, days=min(days, 30))
        
        result = {
            'bot_id': bot_id,
            'bot_name': bot.name,
            'client_id': bot.client_id,
            'client_name': bot.client.name if bot.client else None,
            'period_days': days,
            'usage_stats': stats,
            'daily_usage': daily_usage
        }
        
        return jsonify(result)
        
    except Exception as e:
        logging.error(f"Error getting bot usage: {e}")
        return jsonify({'error': 'Failed to get bot usage'}), 500

@app.route('/api/clients/<int:client_id>/token-limit', methods=['GET', 'PUT'])
def manage_client_token_limit(client_id):
    """Get or set token limit for a client"""
    try:
        client = Client.query.get_or_404(client_id)
        
        if request.method == 'GET':
            limit_status = usage_service.check_client_limits(client_id)
            return jsonify({
                'client_id': client_id,
                'token_limit': client.token_limit,
                'limit_status': limit_status
            })
        
        elif request.method == 'PUT':
            data = request.json
            new_limit = data.get('token_limit')
            
            if new_limit is not None and new_limit < 0:
                return jsonify({'error': 'Token limit must be positive or null'}), 400
            
            client.token_limit = new_limit
            db.session.commit()
            
            return jsonify({
                'message': 'Token limit updated successfully',
                'client_id': client_id,
                'token_limit': client.token_limit
            })
            
    except Exception as e:
        logging.error(f"Error managing token limit for client {client_id}: {e}")
        return jsonify({'error': 'Failed to manage token limit'}), 500

@app.route('/api/cost-rates', methods=['GET'])
def get_cost_rates():
    """Get current OpenAI cost rates configuration"""
    try:
        from utils.cost_calculator import cost_calculator
        rates = cost_calculator.get_rates()
        return jsonify(rates)
    except Exception as e:
        logging.error(f"Error getting cost rates: {e}")
        return jsonify({'error': 'Failed to get cost rates'}), 500


# === ALTERNATIVE DEPLOYMENT ROUTES (Enhanced version for client-linked bots) ===

@app.route('/api/bots/<int:bot_id>/status', methods=['GET'])
def get_bot_deployment_status(bot_id):
    """Get deployment status for a specific bot"""
    try:
        bot = Bot.query.get_or_404(bot_id)
        return jsonify({
            'success': True,
            'bot_id': bot_id,
            'deployment_status': bot.deployment_status or {}
        })
    except Exception as e:
        logging.error(f"Error getting bot status for {bot_id}: {e}")
        return jsonify({'error': 'Failed to get bot status'}), 500

@app.route('/api/bots/<int:bot_id>/deployments', methods=['GET'])
def get_bot_deployments(bot_id):
    """Get all deployments for a bot"""
    try:
        deployments = platform_service.get_bot_deployments(bot_id)
        return jsonify({'deployments': deployments})
    except Exception as e:
        logging.error(f"Error getting deployments for bot {bot_id}: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/deployments/<deployment_id>/stop', methods=['POST'])
def stop_deployment(deployment_id):
    """Stop/Delete a specific deployment"""
    try:
        result = platform_service.stop_deployment(deployment_id)
        if result.get('success'):
            return jsonify(result)
        else:
            return jsonify(result), 400
    except Exception as e:
        logging.error(f"Error stopping deployment {deployment_id}: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/bots/<int:bot_id>/deployments/cleanup', methods=['POST'])
def cleanup_bot_deployments(bot_id):
    """Clean up duplicate deployments for a bot"""
    try:
        from models import Deployment
        
        # Get all deployments for this bot
        deployments = Deployment.query.filter_by(bot_id=bot_id).order_by(Deployment.created_at.desc()).all()
        
        # Group by platform and keep only the latest one for each platform
        platform_latest = {}
        deployments_to_delete = []
        
        for deployment in deployments:
            platform = deployment.platform
            if platform not in platform_latest:
                # Keep the first (latest) deployment for each platform
                platform_latest[platform] = deployment
            else:
                # Mark older deployments for deletion
                deployments_to_delete.append(deployment)
        
        # Delete the duplicates
        deleted_count = 0
        for deployment in deployments_to_delete:
            db.session.delete(deployment)
            deleted_count += 1
        
        db.session.commit()
        
        logging.info(f"Cleaned up {deleted_count} duplicate deployments for bot {bot_id}")
        return jsonify({
            'success': True,
            'message': f'Cleaned up {deleted_count} duplicate deployments',
            'deleted_count': deleted_count,
            'remaining_deployments': len(platform_latest)
        })
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error cleaning up deployments for bot {bot_id}: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/webhook-url/<platform>', methods=['GET'])
def get_webhook_url(platform):
    """Get the auto-generated webhook URL for a specific platform"""
    try:
        # Get the base URL from the request
        base_url = request.url_root.rstrip('/')
        
        # Validate platform
        valid_platforms = ['telegram', 'whatsapp', 'facebook', 'instagram']
        if platform.lower() not in valid_platforms:
            return jsonify({'error': f'Invalid platform. Must be one of: {", ".join(valid_platforms)}'}), 400
        
        # Generate platform-specific webhook URL
        webhook_url = f"{base_url}/webhook/{platform.lower()}"
        
        return jsonify({
            'webhook_url': webhook_url,
            'platform': platform,
            'base_url': base_url
        })
        
    except Exception as e:
        logging.error(f"Error generating webhook URL for platform {platform}: {e}")
        return jsonify({'error': 'Failed to generate webhook URL'}), 500

# === ENHANCED DEPLOYMENT ENDPOINT WITH AUTOMATIC WEBHOOK REGISTRATION ===

@app.route('/api/bots/<int:bot_id>/deploy', methods=['POST'])
def deploy_bot_with_webhook_registration(bot_id):
    """Enhanced deployment endpoint that automatically registers webhooks"""
    try:
        bot = Bot.query.get_or_404(bot_id)
        
        if not bot.client_id:
            return jsonify({'error': 'Bot must be linked to a client before deployment'}), 400
        
        client = Client.query.get_or_404(bot.client_id)
        
        # Parse request data
        data = request.json or {}
        platform = data.get('platform', '').lower()
        
        # Validate platform
        if platform not in platform_service.supported_platforms:
            return jsonify({
                'error': f'Platform {platform} not supported. Available: {", ".join(platform_service.supported_platforms)}'
            }), 400
        
        # Get client API keys
        import json
        if isinstance(client.api_keys, str):
            api_keys = json.loads(client.api_keys) if client.api_keys else {}
        else:
            api_keys = client.api_keys or {}
        
        logging.info(f"Using client API keys for bot {bot_id}: {list(api_keys.keys())}")
        
        # Get base webhook URL - force public domain for production
        import os
        
        # Check if we're on Replit production (has REPLIT_DB_URL)
        if os.environ.get('REPLIT_DB_URL') or os.environ.get('REPL_ID'):
            # We're on Replit - use the public domain
            repl_id = os.environ.get('REPL_ID', 'bot-builder-k')
            base_url = f"https://{repl_id}.replit.app"
            logging.info(f"🚀 Replit production detected - using public domain: {base_url}")
        else:
            # Local development - use request URL but warn
            raw_url_root = request.url_root
            base_url = raw_url_root.rstrip('/') if raw_url_root else None
            logging.warning(f"⚠️ Local development detected: {base_url}. Webhook may not work.")
        
        if not base_url:
            logging.error("ERROR: Unable to determine base URL for webhook registration!")
            # Use environment variable or localhost fallback
            base_url = os.environ.get('REPL_URL', 'http://localhost:5000')
        
        logging.info(f"Using webhook base URL: {base_url}")
        
        # Deploy with automatic webhook registration
        logging.info(f"Calling platform_service.deploy_bot with webhook_base_url: {base_url}")
        result = platform_service.deploy_bot(
            bot_id=bot_id,
            platform=platform,
            api_keys=api_keys,
            webhook_base_url=base_url
        )
        
        logging.info(f"Platform service result: {result}")
        
        if result.get('success'):
            # Update bot deployment status
            try:
                current_status = bot.deployment_status or {}
                current_status[platform] = {
                    'deployed': True,
                    'last_deployed': datetime.utcnow().isoformat(),
                    'webhook_url': result.get('webhook_url'),
                    'webhook_status': result.get('webhook_status', 'registered'),
                    'deployment_id': result.get('deployment_id')
                }
                bot.deployment_status = current_status
                db.session.commit()
                logging.info(f"Updated deployment status for bot {bot_id}: {current_status}")
            except Exception as status_error:
                logging.error(f"Error updating deployment status: {status_error}")
                # Continue with deployment success even if status update fails
            
            logging.info(f"Successfully deployed bot {bot_id} to {platform} with webhook registration")
            return jsonify({
                'success': True,
                'message': f'Bot deployed to {platform} successfully',
                'deployment_id': result.get('deployment_id'),
                'webhook_url': result.get('webhook_url'),
                'webhook_status': result.get('webhook_status', 'registered'),
                'platform_info': result.get('bot_info') or result.get('account_info') or result.get('page_info') or result.get('phone_info'),
                'note': result.get('note'),
                'deployment_status': current_status
            })
        else:
            # Update bot deployment status to failed
            current_status = bot.deployment_status or {}
            current_status[platform] = {
                'deployed': False,
                'last_attempt': datetime.utcnow().isoformat(),
                'error': result.get('error', 'Deployment failed'),
                'webhook_status': result.get('webhook_status', 'failed')
            }
            bot.deployment_status = current_status
            db.session.commit()
            
            logging.error(f"Failed to deploy bot {bot_id} to {platform}: {result.get('error')}")
            return jsonify({
                'success': False,
                'error': result.get('error', 'Deployment failed'),
                'webhook_status': result.get('webhook_status', 'failed'),
                'deployment_status': current_status
            }), 400
            
    except Exception as e:
        logging.error(f"Error in enhanced deployment for bot {bot_id}: {e}")
        import traceback
        logging.error(f"Full traceback: {traceback.format_exc()}")
        return jsonify({'error': f'Deployment failed: {str(e)}'}), 500

# === SIMPLE TEST ROUTE FIRST ===

@app.route('/test/simple')
def simple_test():
    """Simple test route to verify routing works"""
    return 'Simple route works!', 200

@app.route('/test/webhook', methods=['POST', 'GET'])
def test_webhook():
    """Test webhook route"""
    if request.method == 'GET':
        return 'Test webhook GET works', 200
    else:
        return 'Test webhook POST works', 200

# === WORKING BOT WEBHOOK SOLUTION ===

@app.route('/bot/webhook', methods=['POST', 'GET'])
def working_bot_webhook():
    """Simplified working webhook that bypasses the KnowledgeService issue entirely"""
    
    if request.method == 'GET':
        return 'Bot webhook is active and ready!', 200
    
    try:
        data = request.get_json(force=True) or {}
        msg = data.get('message', {})
        text = msg.get('text', '')
        chat = msg.get('chat', {})
        chat_id = chat.get('id')
        
        if text and chat_id:
            import os
            import requests
            from openai import OpenAI
            
            # Get OpenAI API key
            api_key = os.environ.get("OPENAI_API_KEY")
            bot_token = "8301717846:AAFhv9n1qlizTvYytBWVeRZFCAgVqTgGflM"
            
            if api_key:
                # Generate AI response
                try:
                    client = OpenAI(api_key=api_key)
                    
                    response = client.chat.completions.create(
                        model="gpt-4o",
                        messages=[
                            {"role": "system", "content": "You are a helpful AI assistant for a home services business. You help customers with mounting TVs, installing soundbars, and other home tech services. Be friendly, professional, and helpful."},
                            {"role": "user", "content": text}
                        ],
                        max_tokens=400,
                        temperature=0.7
                    )
                    
                    response_text = response.choices[0].message.content
                except Exception as ai_error:
                    response_text = f"Hello! I'm your AI assistant for home services. I can help with TV mounting, soundbar installation, and more. (Note: AI response temporarily unavailable: {str(ai_error)[:50]})"
            else:
                response_text = "Hello! I'm your AI assistant for home services. I can help with TV mounting, soundbar installation, and more. Please configure the OpenAI API key for intelligent responses."
            
            # Send response via Telegram API
            telegram_api = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            payload = {
                "chat_id": chat_id, 
                "text": response_text,
                "parse_mode": "Markdown"
            }
            
            requests.post(telegram_api, json=payload, timeout=10)
            
        return 'OK', 200
        
    except Exception as e:
        # Return OK to prevent webhook retry storms
        return 'OK', 200

# === ORIGINAL WEBHOOK (WITH KNOWN ISSUE) ===

@app.route('/webhook/telegram/<int:bot_id>', methods=['POST', 'GET'])
def telegram_webhook(bot_id):
    """Enhanced webhook to trace the actual error source"""
    
    if request.method == 'GET':
        return 'Active', 200
    
    import traceback
    import requests
    import logging
    
    try:
        data = request.get_json(force=True) or {}
        msg = data.get('message', {})
        text = msg.get('text', '')
        chat = msg.get('chat', {})
        chat_id = chat.get('id')
        
        if text and chat_id:
            # Simple direct OpenAI response without any services to isolate the issue
            import os
            from openai import OpenAI
            
            api_key = os.environ.get("OPENAI_API_KEY")
            if api_key:
                client = OpenAI(api_key=api_key)
                
                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": "You are a helpful AI assistant."},
                        {"role": "user", "content": text}
                    ],
                    max_tokens=200
                )
                
                response_text = response.choices[0].message.content
            else:
                response_text = "✅ Bot is working! No OpenAI key configured, but webhook is functioning."
            
            # Send response
            telegram_api = f"https://api.telegram.org/bot8301717846:AAFhv9n1qlizTvYytBWVeRZFCAgVqTgGflM/sendMessage"
            payload = {"chat_id": chat_id, "text": response_text}
            requests.post(telegram_api, json=payload, timeout=10)
            
        return 'OK', 200
        
    except Exception as e:
        # Log the full traceback to find exact error source
        full_traceback = traceback.format_exc()
        logging.error(f"=== ENHANCED WEBHOOK ERROR ===")
        logging.error(f"Error: {str(e)}")
        logging.error(f"Full traceback:\n{full_traceback}")
        logging.error(f"=== END WEBHOOK ERROR ===")
        
        # Also print to console for immediate debugging
        print(f"=== WEBHOOK ERROR DEBUG ===")
        print(f"Error: {str(e)}")
        print(f"Full traceback:\n{full_traceback}")
        print(f"=== END DEBUG ===")
        
        return f'Webhook error: {str(e)}', 500

@app.route('/webhook/facebook/<int:bot_id>', methods=['POST', 'GET'])
def facebook_webhook(bot_id):
    """Handle Facebook Messenger webhook"""
    try:
        if request.method == 'GET':
            # Webhook verification
            verify_token = request.args.get('hub.verify_token')
            challenge = request.args.get('hub.challenge')
            
            # Get expected verify token from bot's client
            bot = Bot.query.get_or_404(bot_id)
            client = Client.query.get_or_404(bot.client_id) if bot.client_id else None
            expected_token = client.api_keys.get('facebook_verify_token', 'llm_bot_builder_verify') if client else None
            
            if verify_token == expected_token:
                return challenge
            return 'Verification failed', 403
        
        # Handle incoming message
        data = request.json
        entries = data.get('entry', [])
        
        for entry in entries:
            messaging = entry.get('messaging', [])
            for message_event in messaging:
                sender_id = message_event.get('sender', {}).get('id')
                message = message_event.get('message', {})
                text = message.get('text', '')
                
                if not text or not sender_id:
                    continue
                
                # Get bot and client info
                bot = Bot.query.get_or_404(bot_id)
                client = Client.query.get_or_404(bot.client_id) if bot.client_id else None
                
                if not client:
                    continue
                
                # Process message (fix incorrect parameters)
                session_id = f"facebook_{sender_id}"
                conversation_history = conversation_service.get_conversation_history(bot.id, session_id)
                
                response_text, token_usage = openai_service.generate_response(
                    bot=bot,
                    message=text,
                    conversation_history=conversation_history,
                    context=""  # Empty context for now to avoid knowledge service issues
                )
                
                # Store conversation
                conversation_service.store_conversation(bot.id, session_id, text, response_text)
                
                response_data = {'response': response_text, 'token_usage': token_usage}
                
                # Send response back
                if response_data.get('response'):
                    page_access_token = client.api_keys.get('facebook_page_access_token')
                    if page_access_token:
                        platform_service.send_facebook_message(
                            page_access_token, sender_id, response_data['response']
                        )
        
        return 'Messages processed', 200
        
    except Exception as e:
        logging.error(f"Facebook webhook error for bot {bot_id}: {e}")
        return 'Webhook error', 500

if __name__ == '__main__':
    # Production security: Never enable debug in production
    debug_mode = config.DEBUG if hasattr(config, 'DEBUG') else False
    app.run(host='0.0.0.0', port=5000, debug=debug_mode)

app.register_blueprint(auth_bp)

@app.before_request
def require_login():
    from flask import request, redirect, session, url_for
    if request.endpoint not in ('auth.login', 'auth.logout') and not request.endpoint.startswith('webhook'):
        if 'admin' not in session:
            return redirect(url_for('auth.login'))
