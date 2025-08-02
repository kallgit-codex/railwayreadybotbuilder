import logging
import re
from models import KnowledgeBase
from services.openai_service import OpenAIService

class KnowledgeService:
    """Service for managing and searching knowledge bases"""
    
    def __init__(self):
        self.openai_service = OpenAIService()
    
    def get_context_for_bot(self, bot_id, query, max_context_length=2000):
        """
        Search and retrieve relevant context from bot's knowledge bases
        
        Args:
            bot_id: ID of the bot
            query: User's query to search for relevant content
            max_context_length: Maximum length of context to return
        """
        try:
            # Get all knowledge bases for the bot
            knowledge_bases = KnowledgeBase.query.filter_by(bot_id=bot_id).all()
            
            if not knowledge_bases:
                return None
            
            # Analyze query to extract keywords
            query_analysis = self.openai_service.analyze_query_intent(query)
            keywords = query_analysis.get('keywords', [])
            
            # Search for relevant content
            relevant_content = []
            
            for kb in knowledge_bases:
                if kb.content:
                    # Simple keyword-based search (could be enhanced with vector search)
                    relevance_score = self._calculate_relevance(kb.content, keywords, query)
                    if relevance_score > 0:
                        relevant_content.append({
                            'content': kb.content,
                            'filename': kb.filename,
                            'score': relevance_score
                        })
            
            if not relevant_content:
                return None
            
            # Sort by relevance and combine content
            relevant_content.sort(key=lambda x: x['score'], reverse=True)
            
            # Build context string
            context_parts = []
            current_length = 0
            
            for item in relevant_content:
                content_preview = item['content'][:1000]  # Limit each piece
                if current_length + len(content_preview) > max_context_length:
                    break
                
                context_parts.append(f"From {item['filename']}:\n{content_preview}")
                current_length += len(content_preview)
            
            return "\n\n---\n\n".join(context_parts) if context_parts else None
            
        except Exception as e:
            logging.error(f"Error getting context for bot {bot_id}: {e}")
            return None
    
    def _calculate_relevance(self, content, keywords, original_query):
        """
        Calculate relevance score for content based on keywords and query
        Simple scoring algorithm - could be enhanced with more sophisticated methods
        """
        if not content:
            return 0
        
        content_lower = content.lower()
        query_lower = original_query.lower()
        score = 0
        
        # Check for exact query match
        if query_lower in content_lower:
            score += 10
        
        # Check for keyword matches
        for keyword in keywords:
            keyword_lower = keyword.lower()
            # Count occurrences of each keyword
            occurrences = len(re.findall(r'\b' + re.escape(keyword_lower) + r'\b', content_lower))
            score += occurrences * 2
        
        # Check for partial matches
        query_words = query_lower.split()
        for word in query_words:
            if len(word) > 3:  # Only consider meaningful words
                if word in content_lower:
                    score += 1
        
        return score
    
    def search_knowledge(self, *args, **kwargs):
        """TEMPORARY: Debug method to trace where this is being called from"""
        import traceback
        logging.error("=== SEARCH_KNOWLEDGE CALLED ===")
        logging.error(f"Args: {args}")
        logging.error(f"Kwargs: {kwargs}")
        logging.error(f"Traceback:\n{traceback.format_stack()}")
        logging.error("=== END SEARCH_KNOWLEDGE DEBUG ===")
        
        # For now, just return an alias to get_context_for_bot
        if args:
            bot_id = args[0] if len(args) > 0 else kwargs.get('bot_id')
            query = args[1] if len(args) > 1 else kwargs.get('query', '')
            return self.get_context_for_bot(bot_id, query)
        return None

    def get_knowledge_summary(self, bot_id):
        """Get a summary of all knowledge bases for a bot"""
        try:
            knowledge_bases = KnowledgeBase.query.filter_by(bot_id=bot_id).all()
            
            summary = {
                'total_files': len(knowledge_bases),
                'file_types': {},
                'total_content_length': 0,
                'files': []
            }
            
            for kb in knowledge_bases:
                # Count file types
                file_type = kb.file_type
                summary['file_types'][file_type] = summary['file_types'].get(file_type, 0) + 1
                
                # Add to total content length
                if kb.content:
                    summary['total_content_length'] += len(kb.content)
                
                # Add file info
                summary['files'].append({
                    'id': kb.id,
                    'filename': kb.filename,
                    'file_type': kb.file_type,
                    'upload_date': kb.upload_date.isoformat(),
                    'content_length': len(kb.content) if kb.content else 0
                })
            
            return summary
            
        except Exception as e:
            logging.error(f"Error getting knowledge summary for bot {bot_id}: {e}")
            return None
