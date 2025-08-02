"""
Enhanced Knowledge Service with chunking, tagging, and advanced management
"""
import os
import json
import re
import logging
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from app import db
from models import KnowledgeFile, KnowledgeChunk, Bot
from utils.file_handler import FileHandler

class EnhancedKnowledgeService:
    """Service for managing enhanced knowledge base with chunking and tagging"""
    
    def __init__(self):
        self.file_handler = FileHandler('uploads')
        self.chunk_size = 800  # Characters per chunk
        self.overlap_size = 100  # Overlap between chunks for context
        
    def upload_knowledge_file(self, bot_id: int, file, tags: List[str] = None) -> Dict:
        """
        Upload and process a knowledge file with chunking
        
        Args:
            bot_id: ID of the bot
            file: Uploaded file object
            tags: Optional list of tags for categorization
            
        Returns:
            Dictionary with upload status and file details
        """
        try:
            # Validate bot exists
            bot = Bot.query.get(bot_id)
            if not bot:
                return {"success": False, "error": "Bot not found"}
            
            # Save file and extract content
            file_path, file_type = self.file_handler.save_file(file)
            content = self.file_handler.extract_text(file_path, file_type)
            
            if not content:
                return {"success": False, "error": "Could not extract content from file"}
            
            # Create knowledge file record
            knowledge_file = KnowledgeFile(
                bot_id=bot_id,
                filename=file.filename,
                filepath=file_path,
                file_size=len(content),
                file_type=file_type,
                tags=json.dumps(tags) if tags else None,
                is_manual=False
            )
            
            db.session.add(knowledge_file)
            db.session.flush()  # Get the ID
            
            # Create chunks
            chunks = self._create_chunks(content)
            chunk_records = []
            
            for i, chunk_content in enumerate(chunks):
                chunk = KnowledgeChunk(
                    file_id=knowledge_file.id,
                    bot_id=bot_id,
                    content=chunk_content,
                    chunk_index=i,
                    token_count=self._estimate_tokens(chunk_content)
                )
                chunk_records.append(chunk)
            
            db.session.add_all(chunk_records)
            db.session.commit()
            
            return {
                "success": True,
                "file": {
                    "id": knowledge_file.id,
                    "filename": knowledge_file.filename,
                    "file_type": knowledge_file.file_type,
                    "file_size": knowledge_file.file_size,
                    "tags": tags or [],
                    "chunk_count": len(chunks),
                    "upload_date": knowledge_file.upload_date.isoformat()
                }
            }
            
        except Exception as e:
            db.session.rollback()
            logging.error(f"Error uploading knowledge file: {e}")
            return {"success": False, "error": str(e)}
    
    def add_manual_knowledge(self, bot_id: int, title: str, content: str, tags: List[str] = None) -> Dict:
        """
        Add manual knowledge snippet without file upload
        
        Args:
            bot_id: ID of the bot
            title: Title for the knowledge snippet
            content: Text content
            tags: Optional list of tags
            
        Returns:
            Dictionary with creation status
        """
        try:
            # Validate bot exists
            bot = Bot.query.get(bot_id)
            if not bot:
                return {"success": False, "error": "Bot not found"}
            
            # Create knowledge file record for manual entry
            knowledge_file = KnowledgeFile(
                bot_id=bot_id,
                filename=f"Manual: {title}",
                filepath="",  # No file path for manual entries
                file_size=len(content),
                file_type="manual",
                tags=json.dumps(tags) if tags else None,
                is_manual=True
            )
            
            db.session.add(knowledge_file)
            db.session.flush()
            
            # Create chunks for manual content
            chunks = self._create_chunks(content)
            chunk_records = []
            
            for i, chunk_content in enumerate(chunks):
                chunk = KnowledgeChunk(
                    file_id=knowledge_file.id,
                    bot_id=bot_id,
                    content=chunk_content,
                    chunk_index=i,
                    token_count=self._estimate_tokens(chunk_content)
                )
                chunk_records.append(chunk)
            
            db.session.add_all(chunk_records)
            db.session.commit()
            
            return {
                "success": True,
                "file": {
                    "id": knowledge_file.id,
                    "filename": knowledge_file.filename,
                    "file_type": knowledge_file.file_type,
                    "file_size": knowledge_file.file_size,
                    "tags": tags or [],
                    "chunk_count": len(chunks),
                    "upload_date": knowledge_file.upload_date.isoformat()
                }
            }
            
        except Exception as e:
            db.session.rollback()
            logging.error(f"Error adding manual knowledge: {e}")
            return {"success": False, "error": str(e)}
    
    def get_bot_knowledge_files(self, bot_id: int) -> List[Dict]:
        """Get all knowledge files for a bot with metadata"""
        try:
            files = KnowledgeFile.query.filter_by(bot_id=bot_id).order_by(KnowledgeFile.upload_date.desc()).all()
            
            result = []
            for file in files:
                tags = json.loads(file.tags) if file.tags else []
                chunk_count = len(file.chunks)
                
                result.append({
                    "id": file.id,
                    "filename": file.filename,
                    "file_type": file.file_type,
                    "file_size": file.file_size,
                    "upload_date": file.upload_date.isoformat(),
                    "tags": tags,
                    "chunk_count": chunk_count,
                    "is_manual": file.is_manual
                })
            
            return result
            
        except Exception as e:
            logging.error(f"Error getting knowledge files: {e}")
            return []
    
    def delete_knowledge_file(self, bot_id: int, file_id: int) -> Dict:
        """Delete a knowledge file and all its chunks"""
        try:
            # Find the file
            knowledge_file = KnowledgeFile.query.filter_by(id=file_id, bot_id=bot_id).first()
            if not knowledge_file:
                return {"success": False, "error": "Knowledge file not found"}
            
            # Delete physical file if it exists
            if knowledge_file.filepath and os.path.exists(knowledge_file.filepath):
                try:
                    os.remove(knowledge_file.filepath)
                except OSError:
                    pass  # File might already be deleted
            
            # Delete from database (chunks will be deleted via cascade)
            db.session.delete(knowledge_file)
            db.session.commit()
            
            return {"success": True, "message": "Knowledge file deleted successfully"}
            
        except Exception as e:
            db.session.rollback()
            logging.error(f"Error deleting knowledge file: {e}")
            return {"success": False, "error": str(e)}
    
    def update_file_tags(self, bot_id: int, file_id: int, tags: List[str]) -> Dict:
        """Update tags for a knowledge file"""
        try:
            knowledge_file = KnowledgeFile.query.filter_by(id=file_id, bot_id=bot_id).first()
            if not knowledge_file:
                return {"success": False, "error": "Knowledge file not found"}
            
            knowledge_file.tags = json.dumps(tags)
            db.session.commit()
            
            return {"success": True, "message": "Tags updated successfully"}
            
        except Exception as e:
            db.session.rollback()
            logging.error(f"Error updating tags: {e}")
            return {"success": False, "error": str(e)}
    
    def get_relevant_context(self, bot_id: int, query: str, max_chunks: int = 5) -> str:
        """
        Get relevant knowledge context for a query using chunking and relevance scoring
        
        Args:
            bot_id: ID of the bot
            query: User query to find relevant context for
            max_chunks: Maximum number of chunks to return
            
        Returns:
            Formatted context string with relevant knowledge
        """
        try:
            # First try to get from KnowledgeChunk table (enhanced system)
            chunks = KnowledgeChunk.query.filter_by(bot_id=bot_id).all()
            
            if chunks:
                # Use enhanced chunking system
                scored_chunks = []
                query_words = set(query.lower().split())
                
                for chunk in chunks:
                    content_words = set(chunk.content.lower().split())
                    score = len(query_words.intersection(content_words))
                    
                    # Boost score for exact phrase matches
                    if query.lower() in chunk.content.lower():
                        score += 10
                    
                    if score > 0:
                        scored_chunks.append((score, chunk))
                
                # Sort by relevance score and take top chunks
                scored_chunks.sort(key=lambda x: x[0], reverse=True)
                top_chunks = scored_chunks[:max_chunks]
                
                if top_chunks:
                    context_parts = []
                    for score, chunk in top_chunks:
                        context_parts.append(f"[Knowledge Source]: {chunk.content.strip()}")
                    return "\n\n".join(context_parts)
            
            # Fallback to legacy knowledge_base table
            from models import KnowledgeBase
            legacy_knowledge = KnowledgeBase.query.filter_by(bot_id=bot_id).all()
            
            if not legacy_knowledge:
                return ""
            
            # Score legacy knowledge entries by relevance
            scored_entries = []
            query_words = set(query.lower().split())
            
            for entry in legacy_knowledge:
                content_words = set(entry.content.lower().split())
                score = len(query_words.intersection(content_words))
                
                # Boost score for exact phrase matches
                if query.lower() in entry.content.lower():
                    score += 10
                
                if score > 0:
                    scored_entries.append((score, entry))
            
            # Sort by relevance score and take top entries
            scored_entries.sort(key=lambda x: x[0], reverse=True)
            top_entries = scored_entries[:max_chunks]
            
            if not top_entries:
                # If no specific matches, return first few entries
                top_entries = [(0, entry) for entry in legacy_knowledge[:max_chunks]]
            
            # Format context
            context_parts = []
            for score, entry in top_entries:
                context_parts.append(f"[Knowledge Source]: {entry.content.strip()}")
            
            return "\n\n".join(context_parts)
            
        except Exception as e:
            logging.error(f"Error getting relevant context: {e}")
            return ""
    
    def _create_chunks(self, content: str) -> List[str]:
        """Split content into chunks with overlap"""
        if len(content) <= self.chunk_size:
            return [content]
        
        chunks = []
        start = 0
        
        while start < len(content):
            # Find chunk end
            end = start + self.chunk_size
            
            # If not at the end, try to break at word boundary
            if end < len(content):
                # Look for sentence break first
                sentence_break = content.rfind('.', start, end)
                if sentence_break > start + self.chunk_size // 2:
                    end = sentence_break + 1
                else:
                    # Look for word break
                    word_break = content.rfind(' ', start, end)
                    if word_break > start + self.chunk_size // 2:
                        end = word_break
            
            chunk = content[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            # Move start position with overlap
            start = end - self.overlap_size if end < len(content) else end
        
        return chunks
    
    def _estimate_tokens(self, text: str) -> int:
        """Rough estimation of token count"""
        # Simple estimation: ~4 characters per token
        return len(text) // 4
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract meaningful keywords from text"""
        # Remove common stop words and extract meaningful words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'can', 'this', 'that', 'these', 'those'}
        words = re.findall(r'\b\w+\b', text.lower())
        return [word for word in words if len(word) > 2 and word not in stop_words]
    
    def _calculate_relevance_score(self, content: str, query_words: List[str]) -> float:
        """Calculate relevance score based on keyword matches"""
        content_words = self._extract_keywords(content)
        matches = sum(1 for word in query_words if word in content_words)
        return matches / len(query_words) if query_words else 0