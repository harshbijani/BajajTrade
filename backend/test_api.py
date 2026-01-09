"""
Unit tests for Trading API endpoints
"""
import pytest
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from main import app, db

client = TestClient(app)

class TestInstrumentsAPI:
    """Test cases for Instruments API"""
    
    def test_get_instruments(self):
        """Test fetching list of instruments"""
        response = client.get("/api/v1/instruments")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        
        # Check required fields
        instrument = data[0]
        assert "symbol" in instrument
        assert "exchange" in instrument
        assert "instrumentType" in instrument
        assert "lastTradedPrice" in instrument
        assert instrument["symbol"] in ["AAPL", "TSLA", "IBM"]
    
    def test_instrument_fields(self):
        """Test that instruments have correct fields"""
        response = client.get("/api/v1/instruments")
        data = response.json()
        
        for inst in data:
            assert inst["exchange"] in ["NASDAQ", "NYSE"]
            assert inst["instrumentType"] == "EQUITY"
            assert inst["lastTradedPrice"] > 0

class TestOrdersAPI:
    """Test cases for Orders API"""
    
    def setup_method(self):
        """Reset database before each test"""
        db["orders"] = {}
        db["trades"] = []
        db["portfolio"] = {}
        db["stats"] = {"total_pnl": 0.0}
    
    def test_place_market_buy_order(self):
        """Test placing a market BUY order"""
        order_data = {
            "symbol": "AAPL",
            "quantity": 10,
            "side": "BUY",
            "style": "MARKET"
        }
        response = client.post("/api/v1/orders", json=order_data)
        assert response.status_code == 201
        data = response.json()
        assert "orderId" in data
        assert data["status"] in ["NEW", "PLACED", "EXECUTED"]
    
    def test_place_market_sell_order(self):
        """Test placing a market SELL order"""
        # First buy some shares
        buy_order = {
            "symbol": "AAPL",
            "quantity": 10,
            "side": "BUY",
            "style": "MARKET"
        }
        client.post("/api/v1/orders", json=buy_order)
        
        # Then sell
        sell_order = {
            "symbol": "AAPL",
            "quantity": 5,
            "side": "SELL",
            "style": "MARKET"
        }
        response = client.post("/api/v1/orders", json=sell_order)
        assert response.status_code == 201
    
    def test_place_limit_order(self):
        """Test placing a LIMIT order with price"""
        order_data = {
            "symbol": "TSLA",
            "quantity": 5,
            "side": "BUY",
            "style": "LIMIT",
            "price": 400.0
        }
        response = client.post("/api/v1/orders", json=order_data)
        assert response.status_code == 201
        data = response.json()
        assert "orderId" in data
    
    def test_limit_order_requires_price(self):
        """Test that LIMIT orders require price field"""
        order_data = {
            "symbol": "AAPL",
            "quantity": 10,
            "side": "BUY",
            "style": "LIMIT"
            # Missing price
        }
        response = client.post("/api/v1/orders", json=order_data)
        assert response.status_code == 422  # Validation error
    
    def test_invalid_quantity(self):
        """Test that quantity must be > 0"""
        order_data = {
            "symbol": "AAPL",
            "quantity": 0,
            "side": "BUY",
            "style": "MARKET"
        }
        response = client.post("/api/v1/orders", json=order_data)
        assert response.status_code == 422
    
    def test_invalid_side(self):
        """Test validation of order side"""
        order_data = {
            "symbol": "AAPL",
            "quantity": 10,
            "side": "INVALID",
            "style": "MARKET"
        }
        response = client.post("/api/v1/orders", json=order_data)
        assert response.status_code == 422
    
    def test_invalid_style(self):
        """Test validation of order style"""
        order_data = {
            "symbol": "AAPL",
            "quantity": 10,
            "side": "BUY",
            "style": "INVALID"
        }
        response = client.post("/api/v1/orders", json=order_data)
        assert response.status_code == 422
    
    def test_get_order_status(self):
        """Test fetching order status"""
        # Place an order first
        order_data = {
            "symbol": "IBM",
            "quantity": 5,
            "side": "BUY",
            "style": "MARKET"
        }
        create_response = client.post("/api/v1/orders", json=order_data)
        order_id = create_response.json()["orderId"]
        
        # Get order status
        response = client.get(f"/api/v1/orders/{order_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["orderId"] == order_id
        assert "status" in data
        assert data["status"] in ["NEW", "PLACED", "EXECUTED", "CANCELLED"]
        assert "symbol" in data
        assert "quantity" in data
        assert "side" in data
        assert "style" in data
    
    def test_get_nonexistent_order(self):
        """Test fetching non-existent order"""
        response = client.get("/api/v1/orders/nonexistent-id")
        assert response.status_code == 404

class TestPortfolioAPI:
    """Test cases for Portfolio API"""
    
    def setup_method(self):
        """Reset database before each test"""
        db["orders"] = {}
        db["trades"] = []
        db["portfolio"] = {}
        db["stats"] = {"total_pnl": 0.0}
    
    def test_get_empty_portfolio(self):
        """Test fetching empty portfolio"""
        response = client.get("/api/v1/portfolio")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0
    
    def test_get_portfolio_after_buy(self):
        """Test portfolio after buying shares"""
        # Buy some shares
        order_data = {
            "symbol": "AAPL",
            "quantity": 10,
            "side": "BUY",
            "style": "MARKET"
        }
        client.post("/api/v1/orders", json=order_data)
        
        # Check portfolio
        response = client.get("/api/v1/portfolio")
        assert response.status_code == 200
        data = response.json()
        assert len(data) > 0
        
        holding = data[0]
        assert "symbol" in holding
        assert "quantity" in holding
        assert "averagePrice" in holding
        assert "currentValue" in holding
        assert holding["quantity"] == 10
    
    def test_portfolio_fields(self):
        """Test that portfolio has all required fields"""
        # Buy some shares
        order_data = {
            "symbol": "TSLA",
            "quantity": 5,
            "side": "BUY",
            "style": "MARKET"
        }
        client.post("/api/v1/orders", json=order_data)
        
        response = client.get("/api/v1/portfolio")
        data = response.json()
        
        if len(data) > 0:
            holding = data[0]
            required_fields = ["symbol", "quantity", "averagePrice", "currentValue"]
            for field in required_fields:
                assert field in holding

class TestTradesAPI:
    """Test cases for Trades API"""
    
    def setup_method(self):
        """Reset database before each test"""
        db["orders"] = {}
        db["trades"] = []
        db["portfolio"] = {}
        db["stats"] = {"total_pnl": 0.0}
    
    def test_get_trades(self):
        """Test fetching trades"""
        response = client.get("/api/v1/trades")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_trades_after_execution(self):
        """Test trades appear after order execution"""
        # Place and execute an order
        order_data = {
            "symbol": "IBM",
            "quantity": 3,
            "side": "BUY",
            "style": "MARKET"
        }
        client.post("/api/v1/orders", json=order_data)
        
        # Check trades
        response = client.get("/api/v1/trades")
        data = response.json()
        assert len(data) > 0
        
        trade = data[0]
        assert "id" in trade
        assert "symbol" in trade
        assert "qty" in trade
        assert "price" in trade
        assert "side" in trade

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
