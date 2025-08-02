# LLM Bot Builder

## Overview

LLM Bot Builder is a production-ready, enterprise-grade web application for creating, managing, and deploying AI chatbots across multiple social media platforms. The system enables users to build custom bots with personalized knowledge bases, configure their behavior, and deploy them 24/7 to Instagram, Facebook Messenger, WhatsApp, and Telegram. The platform includes comprehensive client management, advanced knowledge systems with chunking and tagging, detailed usage analytics, and enterprise-grade monitoring and security features for reliable production operations.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

The application follows a modular Flask-based architecture with clear separation of concerns:

### Backend Structure
- **Flask Application**: Core web framework with SQLAlchemy for database operations
- **Service Layer**: Modular services for specific functionalities (OpenAI, Knowledge, Platform)
- **Model Layer**: SQLAlchemy models for data persistence
- **Utility Layer**: Helper classes for file handling and common operations

### Frontend Structure
- **Static Frontend**: HTML/CSS/JavaScript dashboard served directly by Flask
- **Bootstrap-based UI**: Modern, responsive interface with dark theme
- **Single-page Application**: Dynamic content loading without page refreshes

## Key Components

### 1. Bot Management System
- **Purpose**: Create, configure, and manage multiple AI bots
- **Features**: Bot personality configuration, system prompts, temperature settings
- **Rationale**: Centralized bot management allows users to maintain multiple specialized bots

### 2. Knowledge Base Integration
- **Purpose**: Upload and manage custom knowledge sources for each bot
- **Supported Formats**: PDF, TXT, MD, CSV files up to 16MB
- **Text Extraction**: Automated content extraction and storage
- **Search Capability**: Keyword-based relevance scoring for context retrieval

### 3. Conversation Memory System
- **Purpose**: Maintain conversation history for contextual responses
- **Storage**: JSON-based message storage with session management
- **Context Limitation**: Last 10 messages retained for optimal performance
- **Session Management**: Unique session IDs for conversation isolation

### 4. Platform Deployment System
- **Purpose**: Deploy bots to social media platforms
- **Supported Platforms**: Instagram, Facebook Messenger, WhatsApp, Telegram
- **Implementation**: Placeholder architecture ready for platform API integration
- **Status Tracking**: Deployment status monitoring and management

### 5. Client Management System
- **Purpose**: Organize and manage multiple clients with their respective bots
- **Features**: Client creation, API key management, bot-to-client linking
- **Database Integration**: Proper foreign key relationships between clients and bots
- **User Interface**: Dedicated client management panel with CRUD operations
- **API Key Storage**: Secure JSON-based storage of client-specific platform credentials

### 6. OpenAI Integration
- **Model**: GPT-4o (latest OpenAI model as of May 2024)
- **Configuration**: Adjustable temperature settings per bot
- **Context Integration**: Knowledge base content injection into prompts
- **Query Analysis**: Intent extraction for improved knowledge retrieval

## Data Flow

1. **Client Management**: User creates client → API keys stored securely → Client becomes available for bot assignment
2. **Bot Creation**: User creates bot → Optional client assignment → System stores configuration → Bot becomes available
3. **Knowledge Upload**: User uploads files → System extracts text → Content stored in database
4. **Conversation Flow**: User message → Knowledge search → Context building → OpenAI API call → Response generation → History storage
5. **Deployment Process**: User initiates deployment → Client API keys retrieved → Platform-specific configuration → Deployment tracking → Status updates

## External Dependencies

### Required Services
- **OpenAI API**: GPT-4o model for response generation (API key required)
- **Platform APIs**: Future integration points for social media platforms

### Python Libraries
- **Flask**: Web framework and routing
- **SQLAlchemy**: Database ORM and migrations
- **PyPDF2**: PDF text extraction (optional, graceful degradation)
- **Werkzeug**: File upload handling and security

### Frontend Libraries
- **Bootstrap**: UI framework with dark theme
- **Feather Icons**: Icon system for interface elements

## Deployment Strategy

### Database Configuration
- **Development**: SQLite database for local development
- **Production**: Environment-based DATABASE_URL configuration
- **Connection Management**: Pool recycling and pre-ping for reliability

### File Storage
- **Local Storage**: Upload folder for knowledge base files
- **Security**: Filename sanitization and file type validation
- **Size Limits**: 16MB maximum file size restriction

### Environment Configuration
- **Secret Management**: Environment variables for sensitive data
- **API Keys**: Configurable OpenAI API key
- **Session Security**: Configurable session secret key

### Scalability Considerations
- **Modular Architecture**: Easy addition of new platforms and services
- **Service Separation**: Independent service classes for maintainability
- **Database Design**: Proper relationships and cascading deletes
- **Error Handling**: Comprehensive logging and graceful error recovery

## Production-Ready Enterprise Features

### 1. Configuration Management
- **Purpose**: Secure, environment-based configuration for production deployment
- **Features**: .env file support, validation of required variables, separate dev/prod configs
- **Implementation**: config.py module with Config classes and environment validation

### 2. Comprehensive Error Handling & Logging
- **Purpose**: Enterprise-grade error tracking and system monitoring
- **Features**: Centralized error handling, structured logging, daily log rotation
- **Log Types**: API errors, message exchanges, deployment events, system health
- **Storage**: Organized log files in `/logs` directory with rotation

### 3. Rate Limiting & Security
- **Purpose**: Prevent abuse and protect against excessive API usage
- **Features**: Per-bot rate limiting (60/min, 2/sec), configurable limits
- **Implementation**: In-memory rate limiter with automatic cleanup

### 4. Health Monitoring System
- **Purpose**: Production monitoring and system health checks
- **Endpoints**: `/health` (comprehensive), `/health/quick` (load balancer)
- **Metrics**: Database health, memory usage, disk space, uptime, bot statistics
- **Integration**: Works with load balancers and monitoring systems

### 5. Database Optimization
- **Purpose**: Enhanced performance for production workloads
- **Features**: Optimized indexes, connection pooling, migration scripts
- **Implementation**: Migration system for safe schema updates

### 6. Always-On Deployment Ready
- **Purpose**: Reliable 24/7 operation for production environments
- **Platforms**: Replit Always-On, VPS deployment, Docker support
- **Documentation**: Complete deployment guides and best practices

## Recent Changes (July 27, 2025)

✅ **Deployment Status Tracking System Complete**
- Added deployment_status JSON column to bot table for real-time platform tracking
- Created visual status indicators with platform icons (Telegram, WhatsApp, Facebook, Instagram)
- Implemented automatic status updates during deployment success/failure
- Added `/api/bots/<bot_id>/status` endpoint for real-time status checks
- Enhanced frontend with green/gray deployment badges and hover tooltips
- Status indicators update automatically after deployment without page refresh
- Complete integration between backend deployment tracking and frontend visualization

✅ **Enhanced Deployment System with Automatic Webhook Registration**
- Eliminated manual curl commands for webhook setup during deployment
- Enhanced deployment endpoint automatically registers webhooks for all platforms
- Real-time deployment status indicators with visual feedback
- Comprehensive error handling and validation for production reliability
- Database tracking of webhook URLs, status, and deployment timestamps per platform

✅ **Enhanced Global OpenAI API Key Protection System Complete**
- Created GlobalSettings model with persistent database storage
- Added enhanced settings service with caching, validation, and rollback capabilities
- Implemented confirmation-protected API key changes with validation
- Updated OpenAI service with startup initialization and automatic key refresh
- Added comprehensive protection warnings and fail-safe mechanisms
- Built automatic validation system using test OpenAI calls
- Enhanced frontend with confirmation dialogs and warning banners
- OpenAI key now fully persistent across app restarts with auto-loading
- Comprehensive logging of all key changes and validation events

✅ **API Keys Management Enhancement**
- Added dedicated API Keys section with edit/display modes in client profiles
- All API key fields are fully editable with proper black text on white background
- Added comprehensive form validation and save functionality
- Backend supports complete CRUD operations for client platform API keys
- Keys display as masked dots in view mode for security
- Proper error handling and user feedback for key management operations

✅ **Per-Session Conversation Memory System Complete**
- Implemented session_id column in conversations table for isolated memory
- Updated conversation service with session-based history (limited to 15 messages)
- Added /api/bots/<bot_id>/clear_conversation endpoint with session management
- Frontend now generates unique session IDs and handles conversation clearing
- Each session maintains independent conversation history
- Clear Conversation button properly starts fresh sessions with no memory

✅ **Knowledge Base Integration Fixed**
- Enhanced OpenAI system prompts with mandatory exact pricing instructions
- Bot now correctly uses specific PDF pricing ($99 standard, $149 large TV mounting)
- Knowledge service retrieves 1,359 characters of relevant context per query
- System passes complete knowledge base information to every conversation

✅ **Bot Management Enhancement**
- Added comprehensive "Edit Bot Settings" modal with all configuration options
- Bot personality, tone, system prompt, temperature, and client assignment editable
- Backend API supports complete bot updates including client transfers
- Full CRUD operations available for bot management post-creation

The architecture prioritizes modularity, security, and production reliability, making it straightforward to add new platforms, enhance knowledge processing capabilities, or integrate additional AI models. The comprehensive monitoring and logging ensure reliable 24/7 operation in production environments.