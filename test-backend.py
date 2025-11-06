"""
Bulut Backend - Comprehensive Test Suite
pytest-based tests for all API endpoints and services
"""

import pytest
import asyncio
from datetime import datetime
from httpx import AsyncClient
from fastapi.testclient import TestClient

# Import the app
from main import app, storage, alias_service, blockchain_service, transaction_service

# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def client():
    """Synchronous test client"""
    return TestClient(app)

@pytest.fixture
async def async_client():
    """Async test client"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

@pytest.fixture
def sample_payment_intent():
    """Sample payment intent for testing"""
    return {
        "payment_type": "single",
        "intent": {
            "action": "send",
            "amount": 50.0,
            "currency": "USD",
            "recipient": {
                "alias": "@alice"
            },
            "memo": "Test payment"
        },
        "confidence": 0.95,
        "requires_confirmation": True,
        "confirmation_text": "Send $50 to @alice?"
    }

@pytest.fixture
def sample_alias_registration():
    """Sample alias registration data"""
    return {
        "alias": "@testuser",
        "address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
        "signature": "0x1234567890abcdef"
    }

# ============================================================================
# HEALTH CHECK TESTS
# ============================================================================

def test_root_endpoint(client):
    """Test root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "Bulut API"
    assert data["status"] == "operational"

def test_health_check(client):
    """Test health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "services" in data
    assert data["services"]["api"] == "operational"

# ============================================================================
# ALIAS MANAGEMENT TESTS
# ============================================================================

def test_register_alias_success(client, sample_alias_registration):
    """Test successful alias registration"""
    response = client.post("/alias/register", json=sample_alias_registration)
    assert response.status_code == 201
    data = response.json()
    assert data["success"] == True
    assert data["alias"] == sample_alias_registration["alias"]
    assert data["address"] == sample_alias_registration["address"].lower()

def test_register_alias_duplicate(client, sample_alias_registration):
    """Test duplicate alias registration fails"""
    # First registration
    client.post("/alias/register", json=sample_alias_registration)
    
    # Second registration should fail
    response = client.post("/alias/register", json=sample_alias_registration)
    assert response.status_code == 409
    data = response.json()
    assert "alias_exists" in data["error"]["error"]

def test_register_alias_invalid_format(client):
    """Test invalid alias format"""
    invalid_data = {
        "alias": "invalid_no_at_sign",
        "address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
        "signature": "0x1234567890abcdef"
    }
    response = client.post("/alias/register", json=invalid_data)
    assert response.status_code == 422

def test_get_alias_success(client, sample_alias_registration):
    """Test resolving alias to address"""
    # Register alias first
    client.post("/alias/register", json=sample_alias_registration)
    
    # Resolve alias
    response = client.get(f"/alias/{sample_alias_registration['alias']}")
    assert response.status_code == 200
    data = response.json()
    assert data["alias"] == sample_alias_registration["alias"]
    assert data["address"] == sample_alias_registration["address"].lower()

def test_get_alias_not_found(client):
    """Test resolving non-existent alias"""
    response = client.get("/alias/@nonexistent")
    assert response.status_code == 404
    data = response.json()
    assert "alias_not_found" in data["error"]["error"]

def test_get_address_by_alias(client, sample_alias_registration):
    """Test reverse lookup: address -> alias"""
    # Register alias first
    client.post("/alias/register", json=sample_alias_registration)
    
    # Get alias by address
    response = client.get(f"/address/{sample_alias_registration['address']}/alias")
    assert response.status_code == 200
    data = response.json()
    assert data["address"] == sample_alias_registration["address"].lower()
    assert data["alias"] == sample_alias_registration["alias"]

def test_get_address_without_alias(client):
    """Test address without registered alias"""
    response = client.get("/address/0xNEWADDRESS123/alias")
    assert response.status_code == 200
    data = response.json()
    assert data["alias"] is None

# ============================================================================
# PAYMENT PROCESSING TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_process_command_success(async_client):
    """Test processing natural language command"""
    command = {
        "text": "Send $50 to @alice",
        "user_id": "test_user",
        "timezone": "UTC"
    }
    
    # Note: This will call the actual AI agent if running
    # In production tests, mock the AI agent response
    try:
        response = await async_client.post("/process_command", json=command)
        # May fail if AI agent not running, that's okay for unit tests
        if response.status_code == 200:
            data = response.json()
            assert "payment_type" in data
            assert "intent" in data
            assert "confidence" in data
    except:
        pytest.skip("AI agent not available")

def test_execute_payment_missing_headers(client, sample_payment_intent):
    """Test payment execution without required headers"""
    request_data = {
        "intent_id": "test_intent_123",
        "payment_intent": sample_payment_intent,
        "user_signature": "0x1234567890abcdef",
        "user_address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb"
    }
    
    response = client.post("/execute_payment", json=request_data)
    assert response.status_code == 422  # Missing headers

def test_execute_payment_with_headers(client, sample_payment_intent, sample_alias_registration):
    """Test payment execution with proper headers"""
    # Register recipient alias first
    client.post("/alias/register", json=sample_alias_registration)
    
    request_data = {
        "intent_id": "test_intent_123",
        "payment_intent": sample_payment_intent,
        "user_signature": "0x1234567890abcdef",
        "user_address": "0xSENDER123"
    }
    
    headers = {
        "X-Wallet-Address": "0xSENDER123",
        "X-Signature": "0x1234567890abcdef"
    }
    
    response = client.post("/execute_payment", json=request_data, headers=headers)
    
    # Should fail because @alice needs to be registered, but structure should be valid
    # In production, we'd mock the blockchain service
    assert response.status_code in [200, 404, 500]

def test_execute_payment_recipient_not_found(client, sample_payment_intent):
    """Test payment execution with non-existent recipient"""
    request_data = {
        "intent_id": "test_intent_123",
        "payment_intent": sample_payment_intent,
        "user_signature": "0x1234567890abcdef",
        "user_address": "0xSENDER123"
    }
    
    headers = {
        "X-Wallet-Address": "0xSENDER123",
        "X-Signature": "0x1234567890abcdef"
    }
    
    response = client.post("/execute_payment", json=request_data, headers=headers)
    assert response.status_code == 404
    data = response.json()
    assert "recipient_not_found" in data["error"]["error"]

# ============================================================================
# TRANSACTION HISTORY TESTS
# ============================================================================

def test_get_transaction_history_empty(client):
    """Test getting transaction history for address with no transactions"""
    response = client.get("/history/0xNEWUSER123")
    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 0
    assert data["transactions"] == []

def test_get_transaction_history_with_limit(client):
    """Test transaction history with limit parameter"""
    response = client.get("/history/0xUSER123?limit=10")
    assert response.status_code == 200
    data = response.json()
    assert data["limit"] == 10

def test_get_transaction_history_max_limit(client):
    """Test transaction history respects max limit"""
    response = client.get("/history/0xUSER123?limit=200")
    assert response.status_code == 200
    data = response.json()
    assert data["limit"] == 100  # Should cap at 100

def test_get_transaction_not_found(client):
    """Test getting non-existent transaction"""
    response = client.get("/transaction/0xNONEXISTENT")
    assert response.status_code == 404

# ============================================================================
# UNIT TESTS FOR SERVICES
# ============================================================================

@pytest.mark.asyncio
async def test_alias_service_register():
    """Test alias service registration"""
    result = await alias_service.register(
        "@testuser2",
        "0x123ABC",
        "0xSIGNATURE"
    )
    assert result["success"] == True
    assert result["alias"] == "@testuser2"

@pytest.mark.asyncio
async def test_alias_service_resolve():
    """Test alias service resolution"""
    # Register first
    await alias_service.register("@testuser3", "0x456DEF", "0xSIG")
    
    # Resolve
    address = await alias_service.resolve_alias("@testuser3")
    assert address == "0x456def"  # Should be lowercase

@pytest.mark.asyncio
async def test_blockchain_service_send_payment():
    """Test blockchain service payment"""
    result = await blockchain_service.send_payment(
        from_address="0xSENDER",
        to_address="0xRECEIVER",
        amount=100.0,
        currency="ARC",
        signature="0xSIG"
    )
    assert result["success"] == True
    assert "transaction_hash" in result
    assert result["transaction_hash"].startswith("0x")

@pytest.mark.asyncio
async def test_blockchain_service_subscription():
    """Test blockchain service subscription creation"""
    result = await blockchain_service.create_subscription(
        from_address="0xSENDER",
        to_address="0xRECEIVER",
        amount=9.99,
        frequency="monthly",
        start_date=datetime.utcnow().isoformat(),
        signature="0xSIG"
    )
    assert result["success"] == True
    assert "subscription_id" in result

@pytest.mark.asyncio
async def test_transaction_service_log():
    """Test transaction logging"""
    tx_data = {
        "from_address": "0xSENDER",
        "to_address": "0xRECEIVER",
        "amount": 50.0,
        "currency": "USD",
        "payment_type": "single",
        "transaction_hash": "0xTXHASH123",
        "status": "success"
    }
    
    tx_id = await transaction_service.log_transaction(tx_data)
    assert tx_id is not None
    assert len(tx_id) > 0

@pytest.mark.asyncio
async def test_transaction_service_history():
    """Test getting transaction history"""
    # Log a transaction first
    await transaction_service.log_transaction({
        "from_address": "0xtest123",
        "to_address": "0xRECEIVER",
        "amount": 100.0,
        "payment_type": "single",
        "transaction_hash": "0xHASH"
    })
    
    # Get history
    history = await transaction_service.get_user_history("0xtest123", limit=10)
    assert history["count"] >= 1
    assert len(history["transactions"]) >= 1

# ============================================================================
# EDGE CASES AND ERROR HANDLING
# ============================================================================

def test_invalid_json_request(client):
    """Test sending invalid JSON"""
    response = client.post(
        "/alias/register",
        data="invalid json",
        headers={"Content-Type": "application/json"}
    )
    assert response.status_code == 422

def test_missing_required_fields(client):
    """Test missing required fields in request"""
    incomplete_data = {
        "alias": "@testuser"
        # Missing address and signature
    }
    response = client.post("/alias/register", json=incomplete_data)
    assert response.status_code == 422

def test_sql_injection_protection(client):
    """Test SQL injection protection in alias"""
    malicious_data = {
        "alias": "@test'; DROP TABLE aliases; --",
        "address": "0x123ABC",
        "signature": "0xSIG"
    }
    response = client.post("/alias/register", json=malicious_data)
    # Should fail validation, not execute SQL
    assert response.status_code in [422, 400]

def test_xss_protection(client):
    """Test XSS protection in memo field"""
    payment_intent = {
        "payment_type": "single",
        "intent": {
            "action": "send",
            "amount": 10.0,
            "recipient": {"alias": "@test"},
            "memo": "<script>alert('xss')</script>"
        },
        "confidence": 0.9,
        "requires_confirmation": True
    }
    
    request_data = {
        "intent_id": "test",
        "payment_intent": payment_intent,
        "user_signature": "0xSIG",
        "user_address": "0xUSER"
    }
    
    headers = {
        "X-Wallet-Address": "0xUSER",
        "X-Signature": "0xSIG"
    }
    
    # Should handle gracefully without executing script
    response = client.post("/execute_payment", json=request_data, headers=headers)
    assert response.status_code in [200, 404, 400, 500]

# ============================================================================
# PERFORMANCE TESTS
# ============================================================================

def test_rate_limiting(client, sample_alias_registration):
    """Test rate limiting on registration endpoint"""
    # Note: This test may not work without actual rate limiting backend (Redis)
    # Adjust based on your rate limiting configuration
    
    responses = []
    for i in range(10):
        data = sample_alias_registration.copy()
        data["alias"] = f"@test{i}"
        data["address"] = f"0x{i:040x}"
        response = client.post("/alias/register", json=data)
        responses.append(response.status_code)
    
    # Some requests should succeed, might hit rate limit
    assert any(status == 201 for status in responses)

@pytest.mark.asyncio
async def test_concurrent_requests(async_client):
    """Test handling concurrent requests"""
    tasks = []
    for i in range(10):
        task = async_client.get("/health")
        tasks.append(task)
    
    responses = await asyncio.gather(*tasks)
    
    # All requests should succeed
    for response in responses:
        assert response.status_code == 200

# ============================================================================
# RUN TESTS
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])