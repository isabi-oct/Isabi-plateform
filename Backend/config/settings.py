import os
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Database
    database_url: str = "sqlite:///./isabi_local.db"
    
    # WhatsApp API
    whatsapp_token: str = os.getenv("WHATSAPP_TOKEN", "")
    whatsapp_verify_token: str = os.getenv("WHATSAPP_VERIFY_TOKEN", "")
    whatsapp_phone_number_id: str = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "")
    default_recipient: str = os.getenv("DEFAULT_RECIPIENT", "")
    
    # Gemini API (replacing OpenAI)
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")
    
    # Flutterwave Payment Integration
    flutterwave_public_key: str = os.getenv("FLUTTERWAVE_PUBLIC_KEY", "")
    flutterwave_secret_key: str = os.getenv("FLUTTERWAVE_SECRET_KEY", "")
    flutterwave_encryption_key: str = os.getenv("FLUTTERWAVE_ENCRYPTION_KEY", "")
    flutterwave_base_url: str = os.getenv("FLUTTERWAVE_BASE_URL", "https://api.flutterwave.com")
    flutterwave_currency: str = os.getenv("FLUTTERWAVE_CURRENCY", "USD")
    flutterwave_timeout: int = int(os.getenv("FLUTTERWAVE_TIMEOUT", "30"))
    
    # App Base URL for callbacks
    app_base_url: str = os.getenv("APP_BASE_URL", "https://your-domain.com")
    
    # Redis
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    
    # GCP Configuration
    gcp_project_id: str = os.getenv("GOOGLE_CLOUD_PROJECT", "")
    gcp_location: str = os.getenv("GCP_LOCATION", "us-central1")
    gcp_credentials_path: str = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "")
    
    # App Settings
    app_name: str = "Isabi WhatsApp Sales Bot"
    debug: bool = os.getenv("DEBUG", "False").lower() == "true"
    payment_link_expiry_minutes: int = 5
    
    class Config:
        env_file = ".env"

settings = Settings()
