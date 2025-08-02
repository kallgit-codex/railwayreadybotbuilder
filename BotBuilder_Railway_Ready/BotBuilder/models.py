from app import db
from datetime import datetime
from sqlalchemy import JSON
import json

class Client(db.Model):
    """Model for managing clients and their API configurations"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    notes = db.Column(db.Text)
    api_keys = db.Column(db.Text)  # JSON string for API keys
    token_limit = db.Column(db.Integer)  # Optional token limit per month
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    bots = db.relationship('Bot', back_populates='client', lazy=True, cascade='all, delete-orphan')
    usage_records = db.relationship('Usage', back_populates='client', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'notes': self.notes,
            'api_keys': json.loads(self.api_keys) if self.api_keys else {},
            'token_limit': self.token_limit,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'bot_count': len(self.bots) if self.bots else 0
        }

class Bot(db.Model):
    """Model for AI bots with configuration and personality settings"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    personality = db.Column(db.Text, default='helpful and friendly')
    personality_description = db.Column(db.Text)  # Enhanced detailed personality
    tone = db.Column(db.String(50), default='friendly')  # friendly, professional, humorous, etc.
    system_prompt = db.Column(db.Text)
    temperature = db.Column(db.Float, default=0.7)
    deployment_status = db.Column(JSON, default=dict)  # Track deployment status per platform
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Foreign key to link bot to client
    client_id = db.Column(db.Integer, db.ForeignKey('client.id'), nullable=True)
    
    # Relationships
    client = db.relationship('Client', back_populates='bots')
    knowledge_bases = db.relationship('KnowledgeBase', backref='bot', lazy=True, cascade='all, delete-orphan')
    conversations = db.relationship('Conversation', backref='bot', lazy=True, cascade='all, delete-orphan')
    deployments = db.relationship('Deployment', backref='bot', lazy=True, cascade='all, delete-orphan')
    usage_records = db.relationship('Usage', back_populates='bot', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'personality': self.personality,
            'personality_description': self.personality_description,
            'tone': self.tone,
            'system_prompt': self.system_prompt,
            'temperature': self.temperature,
            'deployment_status': self.deployment_status or {},
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'client_id': self.client_id,
            'client_name': self.client.name if self.client else None
        }

class KnowledgeBase(db.Model):
    """Model for storing uploaded knowledge base files and content"""
    id = db.Column(db.Integer, primary_key=True)
    bot_id = db.Column(db.Integer, db.ForeignKey('bot.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    file_type = db.Column(db.String(50), nullable=False)
    content = db.Column(db.Text)
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)

# Enhanced knowledge management models
class KnowledgeFile(db.Model):
    """Enhanced file metadata table for better knowledge management"""
    __tablename__ = 'knowledge_files'
    
    id = db.Column(db.Integer, primary_key=True)
    bot_id = db.Column(db.Integer, db.ForeignKey('bot.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    filepath = db.Column(db.String(500), nullable=False)
    file_size = db.Column(db.Integer, nullable=True)
    file_type = db.Column(db.String(50), nullable=False)
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)
    tags = db.Column(db.Text, nullable=True)  # JSON string of tags
    is_manual = db.Column(db.Boolean, default=False)  # For manual text snippets
    
    # Relationship to chunks
    chunks = db.relationship('KnowledgeChunk', backref='file', cascade='all, delete-orphan')

class KnowledgeChunk(db.Model):
    """Content chunks for better context retrieval"""
    __tablename__ = 'knowledge_chunks'
    
    id = db.Column(db.Integer, primary_key=True)
    file_id = db.Column(db.Integer, db.ForeignKey('knowledge_files.id'), nullable=False)
    bot_id = db.Column(db.Integer, db.ForeignKey('bot.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    chunk_index = db.Column(db.Integer, nullable=False)  # Order within file
    token_count = db.Column(db.Integer, nullable=True)  # Estimated tokens
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Conversation(db.Model):
    """Model for storing conversation history with memory"""
    id = db.Column(db.Integer, primary_key=True)
    bot_id = db.Column(db.Integer, db.ForeignKey('bot.id'), nullable=False)
    session_id = db.Column(db.String(100), nullable=False)
    messages = db.Column(JSON, default=list)  # Store conversation as JSON array
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (db.UniqueConstraint('bot_id', 'session_id'),)

class Deployment(db.Model):
    """Model for tracking bot deployments to various platforms"""
    id = db.Column(db.Integer, primary_key=True)
    bot_id = db.Column(db.Integer, db.ForeignKey('bot.id'), nullable=False)
    platform = db.Column(db.String(50), nullable=False)  # instagram, facebook, whatsapp, telegram
    deployment_id = db.Column(db.String(100))
    status = db.Column(db.String(50), default='pending')  # pending, active, failed, stopped
    config = db.Column(JSON)  # Platform-specific configuration
    webhook_url = db.Column(db.String(500))  # Registered webhook URL
    webhook_status = db.Column(db.String(50), default='pending')  # pending, registered, failed
    last_deployed = db.Column(db.DateTime, default=datetime.utcnow)  # When webhook was last set
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Usage(db.Model):
    """Model for tracking token usage and costs per client and bot"""
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('client.id'), nullable=False)
    bot_id = db.Column(db.Integer, db.ForeignKey('bot.id'), nullable=False)
    
    # Token usage tracking - detailed breakdown
    input_tokens = db.Column(db.Integer, default=0)  # Input/prompt tokens
    output_tokens = db.Column(db.Integer, default=0)  # Output/completion tokens
    total_tokens = db.Column(db.Integer, default=0)  # Total tokens used
    
    # Legacy fields for backward compatibility
    tokens_used = db.Column(db.Integer, nullable=False, default=0)
    prompt_tokens = db.Column(db.Integer, default=0)
    completion_tokens = db.Column(db.Integer, default=0)
    
    # Cost calculation (in USD) with detailed breakdown
    input_cost = db.Column(db.Float, default=0.0)  # Cost for input tokens
    output_cost = db.Column(db.Float, default=0.0)  # Cost for output tokens
    total_cost = db.Column(db.Float, default=0.0)  # Total cost for this usage
    
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    client = db.relationship('Client', back_populates='usage_records')
    bot = db.relationship('Bot', back_populates='usage_records')
    
    def to_dict(self):
        return {
            'id': self.id,
            'client_id': self.client_id,
            'bot_id': self.bot_id,
            'input_tokens': self.input_tokens,
            'output_tokens': self.output_tokens,
            'total_tokens': self.total_tokens,
            'input_cost': self.input_cost,
            'output_cost': self.output_cost,
            'total_cost': self.total_cost,
            # Legacy fields
            'tokens_used': self.tokens_used,
            'prompt_tokens': self.prompt_tokens,
            'completion_tokens': self.completion_tokens,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'client_name': self.client.name if self.client else None,
            'bot_name': self.bot.name if self.bot else None
        }


class GlobalSettings(db.Model):
    """Model for storing global application settings"""
    __tablename__ = 'global_settings'
    
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(255), unique=True, nullable=False)
    value = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'key': self.key,
            'value': self.value,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f'<GlobalSettings {self.key}>'
