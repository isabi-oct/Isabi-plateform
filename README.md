# Isabi Agentic AI WhatsApp Sales Bot

A sophisticated **Agentic AI-driven** WhatsApp sales bot that provides autonomous reasoning, intelligent product recommendations, automated sales processes, and seamless payment integration using **LangChain + Vertex AI (Gemini 1.5)**.

## 🏗️ Architecture

This project uses a **true Agentic AI architecture** with autonomous reasoning capabilities:

- **Core Agent**: Main orchestrator with LangChain + Vertex AI integration
- **Database Tools**: Autonomous database access and ORM operations
- **Payment Tools**: Flutterwave payment processing and verification
- **Vector Search Tools**: Semantic search for AI-related Q&A
- **Product Tools**: AI-trainable product management and tutoring

### Key Features
- **Autonomous Reasoning**: AI can reason about customer needs and take actions
- **Database Access**: Direct ORM calls for user, product, and order management
- **Tool Execution**: External API calls for payments, vector search, and tutoring
- **AI Tutoring**: Personalized learning for AI-trainable products
- **Vector Search**: Semantic product knowledge retrieval

## 📁 Project Structure

```
Isabi-plateform/
├── src/                   # New Agentic AI system
│   ├── agents/
│   │   └── core_agent.py  # Main agentic AI orchestrator
│   └── tools/             # Autonomous tools
│       ├── db_tools.py    # Database operations
│       ├── payment_tools.py # Payment processing
│       ├── vector_search_tools.py # Vector search
│       └── product_tools.py # Product management
├── Backend/               # Legacy backend (maintained)
│   ├── core/agents/       # Original agent system
│   ├── models/database/   # Database models
│   └── services/          # Business services
├── api/                   # API endpoints
│   ├── whatsapp/
│   │   ├── webhook.py     # Original webhook
│   │   └── agentic_webhook.py # New agentic webhook
│   ├── payment/
│   │   └── flutterwave.py
│   ├── products/
│   │   └── catalog.py
│   └── main.py           # Main API router
├── Database/              # Database related
│   ├── PostgreSQL/
│   └── VectorDB/
├── config/                # Configuration files
│   ├── settings.py
│   └── gcp_config.py
├── app.py                 # Main application entry point
├── requirements.txt       # Python dependencies
├── test_agentic_system.py # Test script
├── AGENTIC_AI_README.md   # Detailed agentic AI docs
└── README.md             # This file
```

## 🚀 Features

### Agentic AI System
- **Multi-Agent Architecture**: Specialized agents for different conversation aspects
- **Intelligent Orchestration**: Smart routing between agents based on conversation context
- **Context Awareness**: Maintains conversation state and user preferences
- **Memory Management**: Agents remember previous interactions

### WhatsApp Integration
- **Meta Cloud API**: Full WhatsApp Business API integration
- **Interactive Messages**: Support for buttons, lists, and rich media
- **Webhook Handling**: Real-time message processing
- **Message Templates**: Predefined message templates for common scenarios

### Payment Processing
- **Flutterwave Integration**: Complete payment processing
- **Multiple Payment Methods**: Card, bank transfer, mobile money, PayPal
- **Order Management**: Full order lifecycle management
- **Refund Processing**: Automated refund handling

### Product Management
- **Dynamic Catalog**: Real-time product information
- **AI Recommendations**: Intelligent product suggestions
- **Category Browsing**: Organized product categories
- **Search Functionality**: Advanced product search

### Database Integration
- **PostgreSQL**: Primary database for structured data
- **GCP Vector Search**: Vector database for AI embeddings
- **ORM Integration**: SQLAlchemy for database operations
- **Migration Support**: Database schema management

## 🛠️ Installation

### Prerequisites
- Python 3.10+
- PostgreSQL database
- Google Cloud Platform account (for Vector Search)
- WhatsApp Business API access
- Flutterwave account

### Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd Isabi-plateform
   ```

2. **Create virtual environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Configuration**
   Create a `.env` file in the root directory:
   ```env
   # Database
   DATABASE_URL=postgresql://username:password@host:port/database
   
   # WhatsApp
   WHATSAPP_TOKEN=your_whatsapp_token
   WHATSAPP_PHONE_NUMBER_ID=your_phone_number_id
   WHATSAPP_VERIFY_TOKEN=your_verify_token
   
   # AI
   GEMINI_API_KEY=your_gemini_api_key
   
   # Payment
   FLUTTERWAVE_PUBLIC_KEY=your_public_key
   FLUTTERWAVE_SECRET_KEY=your_secret_key
   FLUTTERWAVE_ENCRYPTION_KEY=your_encryption_key
   
   # GCP
   GOOGLE_CLOUD_PROJECT=your_project_id
   ```

5. **Database Setup**
   ```bash
   # Run database migrations
   alembic upgrade head
   ```

6. **Start the application**
   ```bash
   python app.py
   ```

## 🔧 Configuration

### Agent Configuration
Agents can be configured through the `config/` directory:
- `app_config.yaml`: Application settings
- `database_config.yaml`: Database and vector search configuration
- `logging_config.yaml`: Logging configuration

### Agent Behavior
Each agent has configurable behavior:
- **Conversation Agent**: Greeting patterns, response templates
- **Product Agent**: Search algorithms, recommendation logic
- **Sales Agent**: Sales stages, objection handling
- **Payment Agent**: Payment methods, order processing

## 📊 API Endpoints

### WhatsApp Webhook
- `GET /api/whatsapp/webhook` - Webhook verification
- `POST /api/whatsapp/webhook` - Message processing
- `POST /api/whatsapp/test-agentic` - Test agentic conversation

### Products
- `GET /api/products/products` - Get all products
- `GET /api/products/products/{id}` - Get specific product
- `GET /api/products/search` - Search products
- `GET /api/products/categories` - Get categories

### Payment
- `POST /api/payment/initialize` - Initialize payment
- `POST /api/payment/verify` - Verify transaction
- `POST /api/payment/webhook` - Payment webhook

### Health Check
- `GET /api/health` - System health check
- `GET /api/health/agents` - Agent status
- `GET /api/health/whatsapp` - WhatsApp service status

## 🤖 Agentic AI Usage

### Basic Usage
```python
from agents.orchestrator import agent_orchestrator

# Process a message through the agentic system
response = await agent_orchestrator.process_message(
    user_id="user123",
    message="I want to learn AI",
    context={"conversation_type": "whatsapp"}
)

print(response['response'])
print(response['suggestions'])
```

### Agent Status
```python
# Get system status
status = agent_orchestrator.get_system_status()

# Get specific agent status
agent_status = agent_orchestrator.get_agent_status("product")

# Get conversation status
conversation = agent_orchestrator.get_conversation_status("user123")
```

## 🧪 Testing

### Run Tests
```bash
# Run all tests
pytest

# Run specific test categories
pytest test_api/
pytest test_backend/
pytest test_integration/
```

### Test Agentic System
```bash
# Test agentic conversation
curl -X POST "http://localhost:8000/api/whatsapp/test-agentic" \
  -H "Content-Type: application/json" \
  -d '{"message": "I want to buy a course", "phone_number": "1234567890"}'
```

## 📈 Monitoring

### Health Checks
- System health: `GET /api/health`
- Agent status: `GET /api/health/agents`
- Component status: `GET /api/health/detailed`

### Agent Statistics
- Conversation stats: Available through agent status endpoints
- Sales metrics: Tracked by Sales Agent
- Product analytics: Managed by Product Agent
- Payment statistics: Monitored by Payment Agent

## 🔒 Security

- **Environment Variables**: All sensitive data stored in environment variables
- **Webhook Verification**: WhatsApp webhook signature verification
- **Payment Security**: Flutterwave secure payment processing
- **Database Security**: Encrypted connections and prepared statements

## 🚀 Deployment

### Production Deployment
1. Set up production database
2. Configure production environment variables
3. Set up reverse proxy (nginx)
4. Use process manager (systemd, PM2)
5. Configure SSL certificates
6. Set up monitoring and logging

### Docker Deployment
```bash
# Build Docker image
docker build -t isabi-agentic-bot .

# Run container
docker run -p 8000:8000 --env-file .env isabi-agentic-bot
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
- Create an issue in the repository
- Contact the development team
- Check the documentation

## 🔄 Version History

- **v3.0.0**: Agentic AI architecture implementation
- **v2.0.0**: Enhanced AI integration with GCP Vector Search
- **v1.0.0**: Initial WhatsApp bot implementation