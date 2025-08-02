import logging
from datetime import datetime, timedelta
from sqlalchemy import func, and_
from app import db

class UsageService:
    """Service for managing token usage tracking and analytics"""
    
    def __init__(self):
        # OpenAI GPT-4o pricing per 1K tokens (as of July 2024)
        # Input: $0.005 per 1K tokens, Output: $0.015 per 1K tokens
        self.pricing = {
            'prompt_tokens_per_1k': 0.005,
            'completion_tokens_per_1k': 0.015
        }
    
    def log_usage(self, client_id, bot_id, token_usage):
        """
        Log detailed token usage and costs to the database
        
        Args:
            client_id: ID of the client
            bot_id: ID of the bot
            token_usage: Dict with detailed token and cost information
        """
        try:
            from models import Usage
            
            # Extract detailed token usage
            input_tokens = token_usage.get('input_tokens', 0)
            output_tokens = token_usage.get('output_tokens', 0)
            total_tokens = token_usage.get('total_tokens', 0)
            
            # Extract cost information
            input_cost = token_usage.get('input_cost', 0.0)
            output_cost = token_usage.get('output_cost', 0.0)
            total_cost = token_usage.get('total_cost', 0.0)
            
            usage_record = Usage(
                client_id=client_id,
                bot_id=bot_id,
                # New detailed fields
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                total_tokens=total_tokens,
                input_cost=input_cost,
                output_cost=output_cost,
                total_cost=total_cost,
                # Legacy fields for backward compatibility
                tokens_used=total_tokens,
                prompt_tokens=token_usage.get('prompt_tokens', input_tokens),
                completion_tokens=token_usage.get('completion_tokens', output_tokens),
                timestamp=datetime.utcnow()
            )
            
            db.session.add(usage_record)
            db.session.commit()
            
            logging.info(f"Logged usage: {total_tokens} tokens (in: {input_tokens}, out: {output_tokens}), "
                        f"cost: ${total_cost:.6f} for client {client_id}, bot {bot_id}")
            return usage_record
            
        except Exception as e:
            logging.error(f"Error logging usage: {e}")
            db.session.rollback()
            return None
    
    def get_usage_stats(self, client_id=None, bot_id=None, start_date=None, end_date=None):
        """
        Get usage statistics with optional filters
        
        Args:
            client_id: Filter by client ID
            bot_id: Filter by bot ID
            start_date: Start date for filtering
            end_date: End date for filtering
            
        Returns:
            Dict with usage statistics and cost estimates
        """
        try:
            from models import Usage, Client, Bot
            
            # Build query with filters
            query = db.session.query(Usage)
            
            if client_id:
                query = query.filter(Usage.client_id == client_id)
            if bot_id:
                query = query.filter(Usage.bot_id == bot_id)
            if start_date:
                query = query.filter(Usage.timestamp >= start_date)
            if end_date:
                query = query.filter(Usage.timestamp <= end_date)
            
            # Get aggregated statistics with detailed cost tracking
            stats = query.with_entities(
                func.sum(Usage.total_tokens).label('total_tokens'),
                func.sum(Usage.input_tokens).label('total_input_tokens'),
                func.sum(Usage.output_tokens).label('total_output_tokens'),
                func.sum(Usage.total_cost).label('total_cost'),
                func.sum(Usage.input_cost).label('total_input_cost'),
                func.sum(Usage.output_cost).label('total_output_cost'),
                func.count(Usage.id).label('total_messages'),
                # Legacy fields for backward compatibility
                func.sum(Usage.tokens_used).label('tokens_used'),
                func.sum(Usage.prompt_tokens).label('total_prompt_tokens'),
                func.sum(Usage.completion_tokens).label('total_completion_tokens')
            ).first()
            
            total_tokens = stats.total_tokens or stats.tokens_used or 0
            total_input_tokens = stats.total_input_tokens or 0
            total_output_tokens = stats.total_output_tokens or 0
            total_cost = stats.total_cost or 0.0
            total_input_cost = stats.total_input_cost or 0.0
            total_output_cost = stats.total_output_cost or 0.0
            total_messages = stats.total_messages or 0
            
            # Legacy fields
            total_prompt_tokens = stats.total_prompt_tokens or 0
            total_completion_tokens = stats.total_completion_tokens or 0
            
            # Fallback cost calculation if no costs in database yet
            if total_cost == 0.0 and (total_prompt_tokens > 0 or total_completion_tokens > 0):
                total_cost = self.calculate_cost(total_prompt_tokens, total_completion_tokens)
            
            return {
                'total_tokens': total_tokens,
                'total_input_tokens': total_input_tokens,
                'total_output_tokens': total_output_tokens,
                'total_messages': total_messages,
                'total_cost': round(total_cost, 6),
                'total_input_cost': round(total_input_cost, 6),
                'total_output_cost': round(total_output_cost, 6),
                # Legacy fields for backward compatibility
                'total_prompt_tokens': total_prompt_tokens,
                'total_completion_tokens': total_completion_tokens,
                'cost_estimate': round(total_cost, 6),
                'period': {
                    'start_date': start_date.isoformat() if start_date else None,
                    'end_date': end_date.isoformat() if end_date else None
                }
            }
            
        except Exception as e:
            logging.error(f"Error getting usage stats: {e}")
            return {
                'total_tokens': 0,
                'total_prompt_tokens': 0,
                'total_completion_tokens': 0,
                'total_messages': 0,
                'cost_estimate': 0.0,
                'error': str(e)
            }
    
    def get_client_usage_breakdown(self, client_id, days=30):
        """
        Get usage breakdown by bot for a specific client
        
        Args:
            client_id: Client ID
            days: Number of days to look back (default 30)
            
        Returns:
            List of usage stats per bot
        """
        try:
            from models import Usage, Bot
            
            start_date = datetime.utcnow() - timedelta(days=days)
            
            # Query usage grouped by bot
            bot_usage = db.session.query(
                Usage.bot_id,
                Bot.name.label('bot_name'),
                func.sum(Usage.tokens_used).label('total_tokens'),
                func.sum(Usage.prompt_tokens).label('total_prompt_tokens'),
                func.sum(Usage.completion_tokens).label('total_completion_tokens'),
                func.count(Usage.id).label('total_messages')
            ).join(Bot, Usage.bot_id == Bot.id)\
             .filter(Usage.client_id == client_id)\
             .filter(Usage.timestamp >= start_date)\
             .group_by(Usage.bot_id, Bot.name)\
             .all()
            
            breakdown = []
            for usage in bot_usage:
                cost_estimate = self.calculate_cost(
                    usage.total_prompt_tokens or 0,
                    usage.total_completion_tokens or 0
                )
                
                breakdown.append({
                    'bot_id': usage.bot_id,
                    'bot_name': usage.bot_name,
                    'total_tokens': usage.total_tokens or 0,
                    'total_prompt_tokens': usage.total_prompt_tokens or 0,
                    'total_completion_tokens': usage.total_completion_tokens or 0,
                    'total_messages': usage.total_messages or 0,
                    'cost_estimate': cost_estimate
                })
            
            return breakdown
            
        except Exception as e:
            logging.error(f"Error getting client usage breakdown: {e}")
            return []
    
    def get_daily_usage(self, client_id=None, bot_id=None, days=7):
        """
        Get daily usage statistics for charts/graphs
        
        Args:
            client_id: Optional client filter
            bot_id: Optional bot filter
            days: Number of days to include
            
        Returns:
            List of daily usage data
        """
        try:
            from models import Usage
            
            start_date = datetime.utcnow() - timedelta(days=days)
            
            # Build query
            query = db.session.query(
                func.date(Usage.timestamp).label('date'),
                func.sum(Usage.tokens_used).label('total_tokens'),
                func.sum(Usage.prompt_tokens).label('total_prompt_tokens'),
                func.sum(Usage.completion_tokens).label('total_completion_tokens'),
                func.count(Usage.id).label('total_messages')
            ).filter(Usage.timestamp >= start_date)
            
            if client_id:
                query = query.filter(Usage.client_id == client_id)
            if bot_id:
                query = query.filter(Usage.bot_id == bot_id)
            
            daily_usage = query.group_by(func.date(Usage.timestamp)).order_by(func.date(Usage.timestamp)).all()
            
            result = []
            for usage in daily_usage:
                cost_estimate = self.calculate_cost(
                    usage.total_prompt_tokens or 0,
                    usage.total_completion_tokens or 0
                )
                
                result.append({
                    'date': usage.date.isoformat() if usage.date else None,
                    'total_tokens': usage.total_tokens or 0,
                    'total_prompt_tokens': usage.total_prompt_tokens or 0,
                    'total_completion_tokens': usage.total_completion_tokens or 0,
                    'total_messages': usage.total_messages or 0,
                    'cost_estimate': cost_estimate
                })
            
            return result
            
        except Exception as e:
            logging.error(f"Error getting daily usage: {e}")
            return []
    
    def calculate_cost(self, prompt_tokens, completion_tokens):
        """
        Calculate cost estimate based on token usage
        
        Args:
            prompt_tokens: Number of prompt tokens
            completion_tokens: Number of completion tokens
            
        Returns:
            Float cost estimate in USD
        """
        prompt_cost = (prompt_tokens / 1000) * self.pricing['prompt_tokens_per_1k']
        completion_cost = (completion_tokens / 1000) * self.pricing['completion_tokens_per_1k']
        return round(prompt_cost + completion_cost, 4)
    
    def check_client_limits(self, client_id):
        """
        Check if a client is approaching or exceeding their token limit
        
        Args:
            client_id: Client ID to check
            
        Returns:
            Dict with limit status and warnings
        """
        try:
            from models import Client, Usage
            
            client = Client.query.get(client_id)
            if not client or not client.token_limit:
                return {'has_limit': False}
            
            # Get current month usage
            start_of_month = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            
            monthly_usage = db.session.query(func.sum(Usage.tokens_used)).filter(
                and_(
                    Usage.client_id == client_id,
                    Usage.timestamp >= start_of_month
                )
            ).scalar() or 0
            
            limit = client.token_limit
            usage_percentage = (monthly_usage / limit) * 100 if limit > 0 else 0
            
            status = {
                'has_limit': True,
                'limit': limit,
                'current_usage': monthly_usage,
                'usage_percentage': round(usage_percentage, 2),
                'remaining_tokens': max(0, limit - monthly_usage),
                'is_over_limit': monthly_usage > limit,
                'is_approaching_limit': usage_percentage >= 80,
                'warning_message': None
            }
            
            if status['is_over_limit']:
                status['warning_message'] = f"Client has exceeded their monthly limit by {monthly_usage - limit} tokens"
            elif status['is_approaching_limit']:
                status['warning_message'] = f"Client is approaching their monthly limit ({usage_percentage:.1f}% used)"
            
            return status
            
        except Exception as e:
            logging.error(f"Error checking client limits: {e}")
            return {'has_limit': False, 'error': str(e)}