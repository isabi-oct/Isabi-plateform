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
    
    # Orange Money Payment
    orange_money_merchant_id: str = os.getenv("ORANGE_MONEY_MERCHANT_ID", "")
    orange_money_merchant_key: str = os.getenv("ORANGE_MONEY_MERCHANT_KEY", "")
    orange_money_base_url: str = os.getenv("ORANGE_MONEY_BASE_URL", "https://api.orange.com/orange-money-webpay/cm/v1")
    orange_money_currency: str = "XAF"  # Central African CFA franc
    
    # Redis
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    
    # App Settings
    app_name: str = "Isabi WhatsApp Sales Bot"
    debug: bool = os.getenv("DEBUG", "False").lower() == "true"
    payment_link_expiry_minutes: int = 5
    
    class Config:
        env_file = ".env"

settings = Settings()
