import os
import json
import logging
from typing import Tuple, Dict, Any
from openai import OpenAI
from utils.cost_calculator import cost_calculator

class OpenAIService:
    """Service for handling OpenAI API interactions with persistent key management"""
    
    def __init__(self):
        # Initialize without API key to avoid application context issues
        self.api_key = None
        self.client = None
        self.settings_service = None
        self._startup_complete = False
    
    def initialize_on_startup(self):
        """Initialize the service with persistent settings on app startup"""
        try:
            from services.settings_service import settings_service
            self.settings_service = settings_service
            
            # Load API key from persistent storage
            self.api_key = self.settings_service.get_openai_api_key()
            
            if self.api_key:
                self.client = OpenAI(api_key=self.api_key)
                logging.info("✅ OpenAI service initialized with persistent API key")
            else:
                logging.warning("⚠️ OpenAI service started without API key - bots cannot function until key is configured")
            
            self._startup_complete = True
            
        except Exception as e:
            logging.error(f"Error initializing OpenAI service on startup: {e}")
            self._startup_complete = True
    
    def refresh_api_key(self):
        """Refresh the API key and client (called when key is updated)"""
        try:
            if not self.settings_service:
                from services.settings_service import settings_service
                self.settings_service = settings_service
            
            self.api_key = self.settings_service.get_openai_api_key()
            self.client = OpenAI(api_key=self.api_key) if self.api_key else None
            
            logging.info("🔄 OpenAI API key refreshed from global settings")
            
        except Exception as e:
            logging.error(f"Error refreshing OpenAI API key: {e}")
    
    def is_ready(self):
        """Check if the service is ready to handle requests"""
        return self._startup_complete and self.client is not None and self.api_key is not None
    
    def _get_api_key(self):
        """Get OpenAI API key from global settings or environment"""
        try:
            # Initialize settings service if not already done
            if not self.settings_service:
                from services.settings_service import settings_service
                self.settings_service = settings_service
            
            # First try global settings
            api_key = self.settings_service.get_openai_api_key()
            if api_key:
                return api_key
            
            # Fallback to environment variable
            return os.environ.get("OPENAI_API_KEY")
        except Exception as e:
            logging.error(f"Error getting API key: {e}")
            # Fallback to environment variable if settings service fails
            return os.environ.get("OPENAI_API_KEY")
    
    def _refresh_client(self):
        """Refresh the OpenAI client with the latest API key"""
        self.api_key = self._get_api_key()
        self.client = OpenAI(api_key=self.api_key) if self.api_key else None
        
    def generate_response(self, bot, message, conversation_history=None, context=None):
        """
        Generate a response using OpenAI GPT-4o for the given bot and message
        
        Args:
            bot: Bot model instance with personality and configuration
            message: User's message
            conversation_history: List of previous messages for context
            context: Additional context from knowledge base
            
        Returns:
            tuple: (response_text, token_usage_dict)
        """
        try:
            # Check if service is ready
            if not self.is_ready():
                error_msg = "❌ OpenAI API key not configured. Please set the global OpenAI API key in settings before using bots."
                return error_msg, {
                    'input_tokens': 0,
                    'output_tokens': 0,
                    'total_tokens': 0,
                    'input_cost': 0.0,
                    'output_cost': 0.0,
                    'total_cost': 0.0
                }
            
            # Build system prompt
            system_prompt = self._build_system_prompt(bot, context)
            
            # Build message history
            messages = [{"role": "system", "content": system_prompt}]
            
            # Add conversation history (limit to last 10 messages for context)
            if conversation_history:
                recent_history = conversation_history[-10:] if len(conversation_history) > 10 else conversation_history
                for msg in recent_history:
                    if msg.get('role') in ['user', 'assistant']:
                        messages.append({
                            "role": msg['role'],
                            "content": msg['content']
                        })
            
            # Add current user message
            messages.append({"role": "user", "content": message})
            
            # the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
            # do not change this unless explicitly requested by the user
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=messages,  # type: ignore
                temperature=bot.temperature,
                max_tokens=1000
            )
            
            # Extract detailed token usage information and calculate costs
            usage = response.usage
            input_tokens = usage.prompt_tokens if usage else 0
            output_tokens = usage.completion_tokens if usage else 0
            total_tokens = usage.total_tokens if usage else 0
            
            # Calculate costs using the cost calculator
            costs = cost_calculator.calculate_costs(input_tokens, output_tokens)
            
            # Build comprehensive token usage response
            token_usage = {
                'input_tokens': input_tokens,
                'output_tokens': output_tokens,
                'total_tokens': total_tokens,
                'input_cost': costs['input_cost'],
                'output_cost': costs['output_cost'],
                'total_cost': costs['total_cost'],
                # Legacy fields for backward compatibility
                'prompt_tokens': input_tokens,
                'completion_tokens': output_tokens
            }
            
            response_text = response.choices[0].message.content
            return response_text, token_usage
            
        except Exception as e:
            logging.error(f"OpenAI API error: {e}")
            error_response = f"I apologize, but I'm having trouble processing your request right now. Please try again later."
            # Return error with zero token usage
            return error_response, {'total_tokens': 0, 'prompt_tokens': 0, 'completion_tokens': 0}
    
    def _build_system_prompt(self, bot, context=None):
        """Build comprehensive system prompt with enhanced personality features"""
        prompt_parts = []
        
        # Enhanced personality introduction with tone
        personality_intro = "You are an AI assistant"
        
        # Add tone modifier if available
        if hasattr(bot, 'tone') and bot.tone:
            tone_modifiers = {
                'friendly': 'with a warm and approachable manner',
                'professional': 'with a professional and business-focused approach',
                'humorous': 'with a light-hearted and witty personality',
                'casual': 'with a relaxed and informal style',
                'formal': 'with a formal and respectful communication style',
                'enthusiastic': 'with an energetic and positive attitude'
            }
            tone_desc = tone_modifiers.get(bot.tone, f'with a {bot.tone} tone')
            personality_intro += f" {tone_desc}"
        
        prompt_parts.append(personality_intro + ".")
        
        # Enhanced personality description takes priority
        if hasattr(bot, 'personality_description') and bot.personality_description:
            prompt_parts.append(f"Your detailed personality: {bot.personality_description}")
        elif bot.personality:
            prompt_parts.append(f"Your core personality: {bot.personality}")
        
        # Custom system prompt
        if bot.system_prompt:
            prompt_parts.append(f"Additional instructions: {bot.system_prompt}")
        
        # Knowledge base context - CRITICAL: Must use specific information
        if context:
            prompt_parts.append("=" * 50)
            prompt_parts.append("KNOWLEDGE BASE - USE THIS EXACT INFORMATION:")
            prompt_parts.append(context)
            prompt_parts.append("=" * 50)
            prompt_parts.append("MANDATORY INSTRUCTION: You MUST use the exact pricing and information from the knowledge base above. When asked about prices, quote the EXACT amounts shown. DO NOT CHANGE, ROUND, OR APPROXIMATE ANY PRICES. Examples of CORRECT responses: 'Standard TV mounting is $99', 'Large TV mounting is $149', 'Soundbar mounting is $40'. Never say 'around $100' or 'typically $129' - use only the exact figures from the knowledge base.")
        
        # Default behavior
        if not prompt_parts:
            prompt_parts.append("You are a helpful and friendly AI assistant.")
        
        return "\n\n".join(prompt_parts)
    
    def analyze_query_intent(self, query):
        """
        Analyze the user's query to determine intent and extract keywords
        for knowledge base search
        """
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a query analysis expert. Analyze the user's query and extract the main topics, keywords, and intent. Respond with JSON in this format: {'keywords': ['keyword1', 'keyword2'], 'intent': 'question/request/chat', 'topic': 'main topic'}"
                    },
                    {"role": "user", "content": query}
                ],
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content
            if content:
                result = json.loads(content)
            else:
                raise ValueError("Empty response from OpenAI")
            return result
            
        except Exception as e:
            logging.error(f"Error analyzing query intent: {e}")
            return {
                "keywords": query.split()[:5],  # Fallback to first 5 words
                "intent": "question",
                "topic": "general"
            }

# Standalone function for simple bot responses (MVP compatibility)
def generate_response(bot_id, user_message, context=""):
    """
    Simple standalone function for generating bot responses
    Compatible with MVP requirements while leveraging modern OpenAI API
    """
    try:
        # Get OpenAI API key
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            return "OpenAI API key not configured. Please set OPENAI_API_KEY environment variable."
        
        client = OpenAI(api_key=api_key)
        
        # Build prompt as requested
        prompt = f"Bot ID: {bot_id}\nKnowledge: {context}\nUser: {user_message}\nAI:"
        
        # Use modern OpenAI API (updated from the legacy format in requirements)
        completion = client.chat.completions.create(
            model="gpt-4o",  # Using latest model instead of gpt-4
            messages=[
                {"role": "system", "content": "You are a helpful AI chatbot."},
                {"role": "user", "content": prompt}
            ]
        )
        
        return completion.choices[0].message.content
        
    except Exception as e:
        logging.error(f"Error in generate_response: {e}")
        return f"Sorry, I encountered an error processing your request: {str(e)}"


# Initialize the service
openai_service = OpenAIService()
