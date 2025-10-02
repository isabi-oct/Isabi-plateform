# 🤖 Isabi WhatsApp Sales Bot

A comprehensive AI-powered WhatsApp sales bot built with FastAPI, PostgreSQL, and Gemini AI. This project provides a clean, scalable architecture for building conversational commerce solutions.

## 🏗️ Project Architecture

```
Isabi-plateform/
├── 📁 Config/                          # Configuration Management
│   ├── database_config.yaml            # Database configurations
│   ├── app_config.yaml                 # Application settings
│   ├── logging_config.yaml             # Logging configuration
│   └── .env.template                   # Environment variables template
│
├── 📁 Backend/                         # Core Application Logic
│   ├── core/                           # Main application files
│   │   ├── main.py                     # Primary bot application
│   │   ├── main_enhanced_gemini.py     # Enhanced Gemini integration
│   │   ├── ai/                         # AI-related modules
│   │   ├── whatsapp/                   # WhatsApp integration
│   │   ├── payment/                    # Payment processing
│   │   └── database/                   # Database operations
│   ├── services/                       # Business logic services
│   ├── models/                         # Data models
│   ├── utils/                          # Utility functions
│   └── middleware/                     # Custom middleware
│
├── 📁 Database/                        # Database Management
│   ├── PostgreSQL/                     # PostgreSQL database
│   │   ├── simple_data_viewer.py       # Data viewing tools
│   │   └── view_all_data.py            # Comprehensive data viewer
│   ├── VectorDB/                       # Vector database (ChromaDB)
│   ├── WhatsApp/                       # WhatsApp data storage
│   ├── OrangePayment/                  # Payment transaction storage
│   └── AITutor/                        # AI tutor data storage
│
├── 📁 API/                             # API Endpoints
│   ├── whatsapp/                       # WhatsApp webhook & messaging
│   ├── payment/                        # Payment processing APIs
│   ├── products/                       # Product catalog APIs
│   ├── admin/                          # Admin management APIs
│   └── health/                         # Health check APIs
│
├── 📁 Unit-tests/                      # Testing Suite
│   ├── test_backend/                   # Backend tests
│   ├── test_api/                       # API endpoint tests
│   ├── test_database/                  # Database tests
│   ├── test_integration/               # Integration tests
│   ├── conftest.py                     # Test configuration
│   └── requirements.txt                # Test dependencies
│
├── 📄 requirements.txt                 # Main dependencies
├── 📄 .gitignore                       # Git ignore rules
├── 📄 LICENSE                          # Project license
└── 📄 README.md                        # This file
```

## 🚀 Features

### 🤖 AI-Powered Conversations
- **Gemini 2.0 Flash Experimental** integration
- Context-aware conversations
- Product recommendations
- Natural language processing

### 💬 WhatsApp Integration
- Real-time message handling
- Webhook verification
- Message delivery tracking
- Conversation state management

### 💳 Payment Processing
- Orange Money integration
- Transaction tracking
- Payment verification
- Refund management

### 🗄️ Database Management
- **PostgreSQL** for structured data
- **ChromaDB** for vector embeddings
- Chat history storage
- User session management

### 🔧 Configuration Management
- YAML-based configuration
- Environment variable support
- Centralized settings
- Logging configuration

## 🛠️ Installation

### Prerequisites
- Python 3.10+
- PostgreSQL 13+
- Redis (optional, for caching)

### Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd Isabi-plateform
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**
   ```bash
   cp Config/.env.template .env
   # Edit .env with your actual values
   ```

5. **Run the application**
   ```bash
   python Backend/core/main.py
   ```

## ⚙️ Configuration

### Database Configuration
Edit `Config/database_config.yaml`:
```yaml
postgresql:
  host: "your-postgres-host"
  port: 5432
  database: "your-database"
  username: "your-username"
  password: "your-password"
```

### WhatsApp Configuration
Update your `.env` file:
```env
WHATSAPP_TOKEN=your_whatsapp_token
WHATSAPP_VERIFY_TOKEN=your_verify_token
WHATSAPP_PHONE_NUMBER_ID=your_phone_number_id
```

### Gemini AI Configuration
```env
GEMINI_API_KEY=your_gemini_api_key
```

## 🧪 Testing

### Run Tests
```bash
# Install test dependencies
pip install -r Unit-tests/requirements.txt

# Run all tests
pytest Unit-tests/

# Run specific test categories
pytest Unit-tests/test_backend/
pytest Unit-tests/test_api/
pytest Unit-tests/test_database/
```

### Test Coverage
```bash
pytest --cov=Backend --cov=API --cov=Database Unit-tests/
```

## 📊 API Documentation

### WhatsApp Webhook
- **POST** `/webhook` - WhatsApp message webhook
- **GET** `/webhook` - Webhook verification

### Product APIs
- **GET** `/api/products/` - List all products
- **GET** `/api/products/{id}` - Get product details
- **POST** `/api/products/search` - Search products

### Payment APIs
- **POST** `/api/payment/orange-money` - Process Orange Money payment
- **GET** `/api/payment/transactions` - Get transaction history

## 🔧 Development

### Code Structure
- **Config/**: All configuration files
- **Backend/**: Core application logic
- **Database/**: Database-related modules
- **API/**: REST API endpoints
- **Unit-tests/**: Test suite

### Best Practices
- Use type hints for all functions
- Write comprehensive tests
- Follow PEP 8 style guide
- Document all public APIs
- Use logging for debugging

### Adding New Features
1. Create modules in appropriate directories
2. Add configuration in `Config/`
3. Write tests in `Unit-tests/`
4. Update API endpoints in `API/`
5. Update documentation

## 🚀 Deployment

### Docker Deployment
```bash
# Build Docker image
docker build -t isabi-bot .

# Run container
docker run -p 8000:8000 isabi-bot
```

### Environment Variables
Ensure all required environment variables are set:
- Database credentials
- API keys
- WhatsApp tokens
- Payment credentials

## 📝 Logging

Logs are configured in `Config/logging_config.yaml`:
- Console output for development
- File logging for production
- Error-specific log files
- Rotating log files

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

For support and questions:
- Create an issue in the repository
- Check the troubleshooting guide
- Review the API documentation

## 🔄 Version History

- **v2.0.0** - Enhanced Gemini integration, clean architecture
- **v1.0.0** - Initial release with basic functionality

---

**Built with ❤️ for conversational commerce**
