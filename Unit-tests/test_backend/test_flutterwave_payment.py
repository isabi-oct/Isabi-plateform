"""
Test suite for Flutterwave Payment Service

This module contains comprehensive tests for the Flutterwave payment integration
including payment initialization, verification, webhook handling, and refund processing.

Author: AI Assistant
Created: 2025
"""

import pytest
import json
import hashlib
import hmac
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
from fastapi.testclient import TestClient

from Backend.services.payment_service import FlutterwavePaymentService, payment_service
from Backend.models.database.models import Order, OrderStatus, User, Product
from Backend.config.settings import settings

class TestFlutterwavePaymentService:
    """Test cases for FlutterwavePaymentService class."""
    
    @pytest.fixture
    def payment_service_instance(self):
        """Create a payment service instance for testing."""
        with patch.object(settings, 'flutterwave_public_key', 'test_public_key'), \
             patch.object(settings, 'flutterwave_secret_key', 'test_secret_key'), \
             patch.object(settings, 'flutterwave_encryption_key', 'test_encryption_key'), \
             patch.object(settings, 'flutterwave_base_url', 'https://api.flutterwave.com'), \
             patch.object(settings, 'flutterwave_currency', 'USD'), \
             patch.object(settings, 'flutterwave_timeout', 30), \
             patch.object(settings, 'app_base_url', 'https://test.com'), \
             patch.object(settings, 'payment_link_expiry_minutes', 5):
            return FlutterwavePaymentService()
    
    @pytest.fixture
    def mock_order_data(self):
        """Mock order data for testing."""
        return {
            'amount': 100.0,
            'product_name': 'Test Product',
            'order_id': 123,
            'customer_email': 'test@example.com',
            'customer_name': 'Test User',
            'customer_phone': '+1234567890'
        }
    
    @pytest.fixture
    def mock_flutterwave_response(self):
        """Mock Flutterwave API response."""
        return {
            "status": "success",
            "message": "Payment link created",
            "data": {
                "link": "https://checkout.flutterwave.com/v3/hosted/pay/test123",
                "reference": "FLW_REF_123456789"
            }
        }
    
    def test_payment_service_initialization(self, payment_service_instance):
        """Test payment service initialization."""
        assert payment_service_instance.public_key == 'test_public_key'
        assert payment_service_instance.secret_key == 'test_secret_key'
        assert payment_service_instance.encryption_key == 'test_encryption_key'
        assert payment_service_instance.base_url == 'https://api.flutterwave.com'
        assert payment_service_instance.currency == 'USD'
        assert payment_service_instance.timeout == 30
    
    def test_payment_service_initialization_missing_config(self):
        """Test payment service initialization with missing configuration."""
        with patch.object(settings, 'flutterwave_public_key', ''), \
             patch.object(settings, 'flutterwave_secret_key', 'test_secret_key'), \
             patch.object(settings, 'flutterwave_encryption_key', 'test_encryption_key'):
            with pytest.raises(ValueError, match="Flutterwave configuration is incomplete"):
                FlutterwavePaymentService()
    
    def test_generate_transaction_reference(self, payment_service_instance):
        """Test transaction reference generation."""
        order_id = 123
        tx_ref = payment_service_instance._generate_transaction_reference(order_id)
        
        assert tx_ref.startswith("ISABI_123_")
        assert len(tx_ref) > 10  # Should have timestamp
    
    def test_get_headers(self, payment_service_instance):
        """Test header generation for API requests."""
        headers = payment_service_instance._get_headers()
        
        expected_headers = {
            "Authorization": "Bearer test_secret_key",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        assert headers == expected_headers
    
    @patch('requests.post')
    def test_create_payment_link_success(self, mock_post, payment_service_instance, 
                                       mock_order_data, mock_flutterwave_response):
        """Test successful payment link creation."""
        # Mock successful API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_flutterwave_response
        mock_post.return_value = mock_response
        
        result = payment_service_instance.create_payment_link(**mock_order_data)
        
        assert result["success"] is True
        assert result["payment_link"] == "https://checkout.flutterwave.com/v3/hosted/pay/test123"
        assert result["flutterwave_reference"] == "FLW_REF_123456789"
        assert "transaction_reference" in result
        assert "expires_at" in result
        
        # Verify API call was made correctly
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert call_args[0][0] == "https://api.flutterwave.com/v3/payments"
        assert call_args[1]["headers"]["Authorization"] == "Bearer test_secret_key"
    
    @patch('requests.post')
    def test_create_payment_link_api_error(self, mock_post, payment_service_instance, 
                                         mock_order_data):
        """Test payment link creation with API error."""
        # Mock API error response
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.text = "Bad Request"
        mock_post.return_value = mock_response
        
        result = payment_service_instance.create_payment_link(**mock_order_data)
        
        assert result["success"] is False
        assert "API request failed with status 400" in result["error"]
    
    @patch('requests.post')
    def test_create_payment_link_network_error(self, mock_post, payment_service_instance, 
                                             mock_order_data):
        """Test payment link creation with network error."""
        # Mock network error
        mock_post.side_effect = Exception("Network error")
        
        result = payment_service_instance.create_payment_link(**mock_order_data)
        
        assert result["success"] is False
        assert "Network error occurred" in result["error"]
    
    @patch('requests.get')
    def test_verify_transaction_success(self, mock_get, payment_service_instance):
        """Test successful transaction verification."""
        # Mock successful verification response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "success",
            "data": {
                "id": 123456,
                "status": "successful",
                "amount": 100.0,
                "currency": "USD",
                "customer": {"email": "test@example.com"},
                "payment_type": "card",
                "created_at": "2025-01-01T00:00:00Z",
                "tx_ref": "ISABI_123_20250101000000"
            }
        }
        mock_get.return_value = mock_response
        
        result = payment_service_instance.verify_transaction("123456")
        
        assert result["success"] is True
        assert result["transaction_id"] == 123456
        assert result["status"] == "successful"
        assert result["amount"] == 100.0
        assert result["currency"] == "USD"
        assert result["customer_email"] == "test@example.com"
    
    @patch('requests.get')
    def test_verify_transaction_failed(self, mock_get, payment_service_instance):
        """Test transaction verification failure."""
        # Mock failed verification response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "error",
            "message": "Transaction not found"
        }
        mock_get.return_value = mock_response
        
        result = payment_service_instance.verify_transaction("invalid_id")
        
        assert result["success"] is False
        assert "Transaction not found" in result["error"]
    
    def test_verify_webhook_signature_valid(self, payment_service_instance):
        """Test valid webhook signature verification."""
        payload = {"event": "charge.completed", "data": {"id": 123}}
        payload_json = json.dumps(payload, separators=(',', ':'))
        
        # Create valid signature
        signature = hmac.new(
            'test_secret_key'.encode('utf-8'),
            payload_json.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        result = payment_service_instance._verify_webhook_signature(payload, signature)
        assert result is True
    
    def test_verify_webhook_signature_invalid(self, payment_service_instance):
        """Test invalid webhook signature verification."""
        payload = {"event": "charge.completed", "data": {"id": 123}}
        invalid_signature = "invalid_signature"
        
        result = payment_service_instance._verify_webhook_signature(payload, invalid_signature)
        assert result is False
    
    def test_process_webhook_payment_completed(self, payment_service_instance):
        """Test webhook processing for payment completed event."""
        payload = {
            "event": "charge.completed",
            "data": {
                "id": 123456,
                "tx_ref": "ISABI_123_20250101000000",
                "status": "successful"
            }
        }
        
        # Create valid signature
        payload_json = json.dumps(payload, separators=(',', ':'))
        signature = hmac.new(
            'test_secret_key'.encode('utf-8'),
            payload_json.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        result = payment_service_instance.process_webhook(payload, signature)
        
        assert result["success"] is True
        assert result["message"] == "Payment completed successfully"
        assert result["transaction_id"] == 123456
    
    def test_process_webhook_payment_failed(self, payment_service_instance):
        """Test webhook processing for payment failed event."""
        payload = {
            "event": "charge.failed",
            "data": {
                "id": 123456,
                "tx_ref": "ISABI_123_20250101000000"
            }
        }
        
        # Create valid signature
        payload_json = json.dumps(payload, separators=(',', ':'))
        signature = hmac.new(
            'test_secret_key'.encode('utf-8'),
            payload_json.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        result = payment_service_instance.process_webhook(payload, signature)
        
        assert result["success"] is True
        assert result["message"] == "Payment failed event processed"
        assert result["transaction_id"] == 123456
    
    def test_process_webhook_invalid_signature(self, payment_service_instance):
        """Test webhook processing with invalid signature."""
        payload = {"event": "charge.completed", "data": {"id": 123}}
        invalid_signature = "invalid_signature"
        
        result = payment_service_instance.process_webhook(payload, invalid_signature)
        
        assert result["success"] is False
        assert "Invalid webhook signature" in result["error"]
    
    @patch('requests.post')
    def test_initiate_refund_success(self, mock_post, payment_service_instance):
        """Test successful refund initiation."""
        # Mock successful refund response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "success",
            "data": {
                "id": "refund_123",
                "status": "pending",
                "amount": 50.0
            }
        }
        mock_post.return_value = mock_response
        
        result = payment_service_instance.initiate_refund("tx_123", 50.0, "Customer request")
        
        assert result["success"] is True
        assert result["refund_id"] == "refund_123"
        assert result["status"] == "pending"
        assert result["amount"] == 50.0
    
    @patch('requests.get')
    def test_get_transaction_history_success(self, mock_get, payment_service_instance):
        """Test successful transaction history retrieval."""
        # Mock successful history response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "success",
            "data": [
                {"id": 1, "amount": 100.0, "status": "successful"},
                {"id": 2, "amount": 50.0, "status": "successful"}
            ]
        }
        mock_get.return_value = mock_response
        
        result = payment_service_instance.get_transaction_history("test@example.com", 10)
        
        assert result["success"] is True
        assert len(result["transactions"]) == 2
        assert result["total"] == 2
        assert result["transactions"][0]["id"] == 1


class TestFlutterwavePaymentAPI:
    """Test cases for Flutterwave Payment API endpoints."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        from api.main import app
        return TestClient(app)
    
    @pytest.fixture
    def mock_db_session(self):
        """Create mock database session."""
        session = Mock()
        return session
    
    @pytest.fixture
    def sample_payment_request(self):
        """Sample payment request data."""
        return {
            "amount": 100.0,
            "product_name": "Test Product",
            "order_id": 123,
            "customer_email": "test@example.com",
            "customer_name": "Test User",
            "customer_phone": "+1234567890"
        }
    
    @patch('app.services.payment_service.payment_service.create_payment_link')
    def test_initialize_payment_success(self, mock_create_payment, client, sample_payment_request):
        """Test successful payment initialization."""
        # Mock successful payment service response
        mock_create_payment.return_value = {
            "success": True,
            "payment_link": "https://checkout.flutterwave.com/v3/hosted/pay/test123",
            "transaction_reference": "ISABI_123_20250101000000",
            "flutterwave_reference": "FLW_REF_123456789",
            "expires_at": datetime.utcnow() + timedelta(minutes=5)
        }
        
        response = client.post("/payment/flutterwave/initialize", json=sample_payment_request)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["payment_link"] == "https://checkout.flutterwave.com/v3/hosted/pay/test123"
        assert data["transaction_reference"] == "ISABI_123_20250101000000"
    
    @patch('app.services.payment_service.payment_service.create_payment_link')
    def test_initialize_payment_failure(self, mock_create_payment, client, sample_payment_request):
        """Test payment initialization failure."""
        # Mock failed payment service response
        mock_create_payment.return_value = {
            "success": False,
            "error": "Payment creation failed"
        }
        
        response = client.post("/payment/flutterwave/initialize", json=sample_payment_request)
        
        assert response.status_code == 400
        data = response.json()
        assert "Payment creation failed" in data["detail"]
    
    @patch('app.services.payment_service.payment_service.verify_transaction')
    def test_verify_transaction_success(self, mock_verify, client):
        """Test successful transaction verification."""
        # Mock successful verification response
        mock_verify.return_value = {
            "success": True,
            "transaction_id": 123456,
            "status": "successful",
            "amount": 100.0,
            "currency": "USD",
            "customer_email": "test@example.com",
            "payment_type": "card",
            "created_at": "2025-01-01T00:00:00Z",
            "tx_ref": "ISABI_123_20250101000000"
        }
        
        request_data = {"transaction_id": "123456"}
        response = client.post("/payment/flutterwave/verify", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["transaction_id"] == 123456
        assert data["status"] == "successful"
    
    @patch('app.services.payment_service.payment_service.process_webhook')
    def test_webhook_processing_success(self, mock_process_webhook, client):
        """Test successful webhook processing."""
        # Mock successful webhook processing
        mock_process_webhook.return_value = {
            "success": True,
            "message": "Webhook processed successfully"
        }
        
        payload = {
            "event": "charge.completed",
            "data": {"id": 123456, "tx_ref": "ISABI_123_20250101000000"}
        }
        
        headers = {"verif-hash": "valid_signature"}
        response = client.post("/payment/flutterwave/webhook", json=payload, headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
    
    def test_webhook_missing_signature(self, client):
        """Test webhook processing with missing signature."""
        payload = {"event": "charge.completed", "data": {"id": 123456}}
        
        response = client.post("/payment/flutterwave/webhook", json=payload)
        
        assert response.status_code == 400
        data = response.json()
        assert "Missing webhook signature" in data["detail"]
    
    @patch('app.services.payment_service.payment_service.initiate_refund')
    def test_initiate_refund_success(self, mock_refund, client):
        """Test successful refund initiation."""
        # Mock successful refund response
        mock_refund.return_value = {
            "success": True,
            "refund_id": "refund_123",
            "status": "pending",
            "amount": 50.0
        }
        
        request_data = {
            "transaction_id": "tx_123",
            "amount": 50.0,
            "reason": "Customer request"
        }
        
        response = client.post("/payment/flutterwave/refund", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["refund_id"] == "refund_123"
    
    @patch('app.services.payment_service.payment_service.get_transaction_history')
    def test_get_transaction_history_success(self, mock_history, client):
        """Test successful transaction history retrieval."""
        # Mock successful history response
        mock_history.return_value = {
            "success": True,
            "transactions": [
                {"id": 1, "amount": 100.0, "status": "successful"},
                {"id": 2, "amount": 50.0, "status": "successful"}
            ],
            "total": 2
        }
        
        request_data = {"customer_email": "test@example.com", "limit": 10}
        response = client.post("/payment/flutterwave/history", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["transactions"]) == 2
        assert data["total"] == 2
    
    def test_health_check(self, client):
        """Test health check endpoint."""
        response = client.get("/payment/flutterwave/health")
        
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "service" in data
        assert "timestamp" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
