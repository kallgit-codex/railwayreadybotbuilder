import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
import json

class ConversationService:
    """Service for managing conversation memory and history"""
    
    def __init__(self):
        self.max_context_messages = 10  # Configurable context window
        
    def get_or_create_conversation(self, bot_id: int, session_id: str):
        """Get existing conversation or create new one"""
        # Import here to avoid circular imports
        from models import Conversation, db
        
        conversation = Conversation.query.filter_by(
            bot_id=bot_id, 
            session_id=session_id
        ).first()
        
        if not conversation:
            conversation = Conversation(
                bot_id=bot_id,
                session_id=session_id,
                messages=[]
            )
            db.session.add(conversation)
            db.session.commit()
            
        return conversation
    
    def add_message(self, bot_id: int, session_id: str, role: str, content: str) -> None:
        """Add a message to the conversation"""
        try:
            from models import db
            conversation = self.get_or_create_conversation(bot_id, session_id)
            
            # Get current messages or initialize empty list
            messages = conversation.messages or []
            
            # Add new message
            new_message = {
                'role': role,
                'content': content,
                'timestamp': datetime.utcnow().isoformat()
            }
            messages.append(new_message)
            
            # Keep only recent messages for context (configurable limit)
            if len(messages) > self.max_context_messages * 2:  # *2 for user+bot pairs
                messages = messages[-(self.max_context_messages * 2):]
            
            # Update conversation
            conversation.messages = messages
            conversation.updated_at = datetime.utcnow()
            db.session.commit()
            
        except Exception as e:
            logging.error(f"Error adding message to conversation {bot_id}/{session_id}: {e}")
            db.session.rollback()
    
    def get_conversation_history(self, bot_id: int, session_id: str, limit: int = None) -> List[Dict[str, Any]]:
        """Get conversation history for context, limited to recent messages"""
        try:
            from models import Conversation
            conversation = Conversation.query.filter_by(
                bot_id=bot_id, 
                session_id=session_id
            ).first()
            
            if not conversation or not conversation.messages:
                return []
                
            messages = conversation.messages or []
            
            # Apply limit if specified, otherwise use default max context
            if limit:
                messages = messages[-limit:]
            elif len(messages) > self.max_context_messages * 2:
                messages = messages[-(self.max_context_messages * 2):]
            
            return messages
            
        except Exception as e:
            logging.error(f"Error getting conversation history {bot_id}/{session_id}: {e}")
            return []
    
    def get_full_conversation(self, bot_id: int, session_id: str) -> List[Dict[str, Any]]:
        """Get full conversation for display (not just context)"""
        try:
            from models import Conversation
            conversation = Conversation.query.filter_by(
                bot_id=bot_id, 
                session_id=session_id
            ).first()
            
            if conversation and conversation.messages:
                return conversation.messages or []
            
            return []
            
        except Exception as e:
            logging.error(f"Error getting full conversation {bot_id}/{session_id}: {e}")
            return []
    
    def add_user_and_assistant_messages(self, bot_id: int, session_id: str, user_message: str, assistant_message: str) -> None:
        """Add both user and assistant messages in one transaction"""
        try:
            conversation = self.get_or_create_conversation(bot_id, session_id)
            
            # Get current messages or initialize empty list
            messages = conversation.messages or []
            
            # Add user message
            user_msg = {
                'role': 'user',
                'content': user_message,
                'timestamp': datetime.utcnow().isoformat()
            }
            messages.append(user_msg)
            
            # Add assistant message
            assistant_msg = {
                'role': 'assistant',
                'content': assistant_message,
                'timestamp': datetime.utcnow().isoformat()
            }
            messages.append(assistant_msg)
            
            # Keep only recent messages for context (configurable limit)
            if len(messages) > self.max_context_messages * 2:  # *2 for user+bot pairs
                messages = messages[-(self.max_context_messages * 2):]
            
            # Update conversation
            conversation.messages = messages
            conversation.updated_at = datetime.utcnow()
            db.session.commit()
            
        except Exception as e:
            logging.error(f"Error adding user and assistant messages to conversation {bot_id}/{session_id}: {e}")
            db.session.rollback()

    def clear_conversation(self, bot_id: int, session_id: str) -> bool:
        """Clear conversation history"""
        try:
            conversation = Conversation.query.filter_by(
                bot_id=bot_id, 
                session_id=session_id
            ).first()
            
            if conversation:
                conversation.messages = []
                conversation.updated_at = datetime.utcnow()
                db.session.commit()
                return True
                
            return False
            
        except Exception as e:
            logging.error(f"Error clearing conversation {bot_id}/{session_id}: {e}")
            db.session.rollback()
            return False
    
    def get_bot_conversations(self, bot_id: int) -> List[Dict[str, Any]]:
        """Get all conversation sessions for a bot"""
        try:
            conversations = Conversation.query.filter_by(bot_id=bot_id).all()
            return [
                {
                    'session_id': conv.session_id,
                    'message_count': len(conv.messages) if conv.messages else 0,
                    'created_at': conv.created_at.isoformat() if conv.created_at else None,
                    'updated_at': conv.updated_at.isoformat() if conv.updated_at else None
                }
                for conv in conversations
            ]
            
        except Exception as e:
            logging.error(f"Error getting bot conversations {bot_id}: {e}")
            return []

# Create global instance
conversation_service = ConversationService()