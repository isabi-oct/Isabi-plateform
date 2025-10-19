# Agentic AI System for WhatsApp Product Sales

This document describes the new Agentic AI system that has been implemented to replace the traditional LLM conversational system with autonomous reasoning capabilities.

## Overview

The Agentic AI system uses **LangChain + Vertex AI (Gemini 1.5)** to provide:
- **Autonomous reasoning** about customer messages
- **Database access** through ORM calls
- **External tool execution** for payments, vector search, and AI tutoring
- **Context-aware responses** with memory management

## Architecture

### Core Components

1. **Core Agent** (`src/agents/core_agent.py`)
   - Main agentic AI orchestrator
   - Integrates with LangChain and Vertex AI
   - Manages conversation context and memory
   - Coordinates tool execution

2. **Database Tools** (`src/tools/db_tools.py`)
   - User management (create, search, update)
   - Product management (search, create, update)
   - Order management (create, track, update status)
   - Chat session management
   - AI questions and quizzes management

3. **Payment Tools** (`src/tools/payment_tools.py`)
   - Flutterwave payment link creation
   - Transaction verification
   - Refund processing
   - Payment status tracking
   - Transaction history retrieval

4. **Vector Search Tools** (`src/tools/vector_search_tools.py`)
   - Semantic product knowledge search
   - AI questions and answers search
   - Similar product recommendations
   - Vector index management

5. **Product Tools** (`src/tools/product_tools.py`)
   - AI-trainable product management
   - Tutoring session management
   - Product recommendations
   - Analytics and insights

### Agentic Webhook (`api/whatsapp/agentic_webhook.py`)

The new webhook endpoint that integrates with the agentic system:
- `/whatsapp/agentic/webhook` - Main webhook for WhatsApp messages
- `/whatsapp/agentic/test` - Test endpoint for direct API testing
- `/whatsapp/agentic/status` - System status and health check
- `/whatsapp/agentic/reset/{phone_number}` - Reset conversation for a user

## Key Features

### 1. Autonomous Reasoning
The agent can reason about customer needs and take appropriate actions:
- Analyze customer messages for intent
- Determine appropriate tools to use
- Execute multi-step processes autonomously
- Learn from conversation context

### 2. Database Integration
Full ORM integration for data management:
- User profile management
- Product catalog operations
- Order tracking and management
- Conversation history storage

### 3. Payment Processing
Seamless Flutterwave integration:
- Automatic payment link generation
- Transaction verification
- Refund processing
- Payment status tracking

### 4. AI Tutoring for Trainable Products
Special handling for AI-trainable products:
- Personalized tutoring sessions
- Q&A based on product knowledge
- Vector search for relevant information
- Ongoing support and guidance

### 5. Vector Search
Semantic search capabilities:
- Product knowledge base search
- AI questions and answers
- Similar product recommendations
- Context-aware content retrieval

## Environment Configuration

Create a `.env` file with the following variables:

```env
# Database
DATABASE_URL=sqlite:///./isabi_local.db

# WhatsApp API
WHATSAPP_TOKEN=your_token
WHATSAPP_VERIFY_TOKEN=your_verify_token
WHATSAPP_PHONE_NUMBER_ID=your_phone_id

# AI Configuration
GEMINI_API_KEY=your_gemini_key

# GCP Configuration
GOOGLE_CLOUD_PROJECT=your_project_id
GCP_LOCATION=us-central1
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json

# Flutterwave
FLUTTERWAVE_PUBLIC_KEY=your_public_key
FLUTTERWAVE_SECRET_KEY=your_secret_key
FLUTTERWAVE_ENCRYPTION_KEY=your_encryption_key

# App Configuration
APP_BASE_URL=https://your-domain.com
REDIS_URL=redis://localhost:6379
```

## Usage

### Starting the Agentic System

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment variables (see above)

3. Run the application:
```bash
uvicorn api.main:app --reload
```

### Testing the Agentic System

Use the test endpoint to interact with the agentic AI:

```bash
curl -X POST "http://localhost:8000/whatsapp/agentic/test" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "I want to buy an AI course",
    "phone_number": "+1234567890"
  }'
```

### Webhook Configuration

Configure your WhatsApp webhook to point to:
```
https://your-domain.com/whatsapp/agentic/webhook
```

## Product Types

### Regular Products
- Standard digital products
- Instant access after payment
- Basic customer support

### AI-Trainable Products
- Include personalized AI tutoring
- Ongoing Q&A sessions
- Vector-based knowledge retrieval
- Continuous learning support

## Tool Capabilities

The agent has access to the following tools:

### Database Tools
- `search_users` - Find users by phone, ID, or name
- `create_user` - Create new user accounts
- `search_products` - Find products by various criteria
- `create_order` - Create new orders
- `update_order_status` - Update order status
- `get_chat_session` - Retrieve conversation history

### Payment Tools
- `create_payment_link` - Generate Flutterwave payment links
- `verify_transaction` - Verify payment status
- `initiate_refund` - Process refunds
- `get_payment_status` - Check payment status

### Vector Search Tools
- `search_product_knowledge` - Semantic product search
- `search_ai_questions` - Find relevant Q&A
- `search_similar_products` - Product recommendations
- `semantic_product_search` - Cross-product search

### Product Tools
- `get_ai_tutor_products` - Find AI tutoring products
- `start_tutoring_session` - Begin AI tutoring
- `create_ai_question` - Add Q&A content
- `get_product_recommendations` - Personalized suggestions

## Monitoring and Analytics

### System Status
Check system health:
```bash
curl http://localhost:8000/whatsapp/agentic/status
```

### Analytics
Get system analytics:
```bash
curl http://localhost:8000/whatsapp/agentic/analytics
```

## Migration from Legacy System

The agentic system runs alongside the existing system. To migrate:

1. Update your WhatsApp webhook URL to use the agentic endpoint
2. Test thoroughly with the test endpoint
3. Monitor system performance and user interactions
4. Gradually roll out to all users

## Troubleshooting

### Common Issues

1. **Vector Search Not Working**
   - Ensure GCP credentials are properly configured
   - Check that vector collections exist for products

2. **Payment Processing Fails**
   - Verify Flutterwave credentials
   - Check webhook configuration

3. **Database Connection Issues**
   - Verify DATABASE_URL configuration
   - Ensure database is accessible

### Logs

Check application logs for detailed error information:
```bash
tail -f logs/application.log
```

## Future Enhancements

- Machine learning-based product recommendations
- Advanced conversation analytics
- Multi-language support
- Integration with additional payment providers
- Enhanced AI tutoring features

## Support

For technical support or questions about the agentic AI system, please refer to the system logs or contact the development team.
