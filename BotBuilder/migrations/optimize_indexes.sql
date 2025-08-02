-- Database optimization indexes for LLM Bot Builder
-- Run this after database creation to improve performance

-- Index for bot lookups by client
CREATE INDEX IF NOT EXISTS idx_bot_client_id ON bot(client_id);

-- Index for knowledge file lookups by bot
CREATE INDEX IF NOT EXISTS idx_knowledge_file_bot_id ON knowledge_file(bot_id);

-- Index for knowledge chunk lookups by file
CREATE INDEX IF NOT EXISTS idx_knowledge_chunk_file_id ON knowledge_chunk(knowledge_file_id);

-- Index for conversation lookups by bot and session
CREATE INDEX IF NOT EXISTS idx_conversation_bot_session ON conversation(bot_id, session_id);

-- Index for usage lookups by client and date
CREATE INDEX IF NOT EXISTS idx_usage_client_date ON usage(client_id, created_at);

-- Index for deployment lookups by bot
CREATE INDEX IF NOT EXISTS idx_deployment_bot_id ON deployment(bot_id);

-- Index for usage lookups by bot
CREATE INDEX IF NOT EXISTS idx_usage_bot_id ON usage(bot_id);

-- Composite indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_conversation_bot_updated ON conversation(bot_id, updated_at);
CREATE INDEX IF NOT EXISTS idx_usage_client_bot_date ON usage(client_id, bot_id, created_at);