# Bajaj Trading Platform API

A comprehensive REST API for a simplified trading platform that allows users to view instruments, place orders (MARKET and LIMIT), track order status, view executed trades, and manage portfolio holdings.

## 🚀 Features

- **Instrument Management**: Fetch list of tradable instruments with real-time prices
- **Order Management**: Place BUY/SELL orders (MARKET and LIMIT types)
- **Order Status Tracking**: Track orders through lifecycle (NEW → PLACED → EXECUTED/CANCELLED)
- **Portfolio Management**: View holdings with current values and P&L
- **Trade History**: View all executed trades
- **Real-time Price Simulation**: Geometric Brownian Motion simulation for realistic price movements
- **Swagger/OpenAPI Documentation**: Interactive API documentation
- **Comprehensive Logging**: Centralized logging for all operations
- **Error Handling**: Proper HTTP status codes and error messages
- **Unit Tests**: Test coverage for critical APIs

## 📋 Technology Stack

- **Backend Framework**: FastAPI (Python 3.9+)
- **API Format**: JSON (REST)
- **Data Storage**: In-memory (Python dictionaries)
- **Testing**: pytest
- **Documentation**: Swagger/OpenAPI (auto-generated)

## 🛠️ Setup and Installation

### Prerequisites

- Python 3.9 or higher
- pip (Python package manager)

### Installation Steps

1. **Clone the repository**
   ```bash
   cd TradeBajaj1
   ```

2. **Create a virtual environment (recommended)**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Start the backend server**
   ```bash
   cd backend
   uvicorn main:app --reload --host 127.0.0.1 --port 8000
   ```

   The API will be available at: `http://127.0.0.1:8000`

5. **Access API Documentation**
   - Swagger UI: `http://127.0.0.1:8000/docs`
   - ReDoc: `http://127.0.0.1:8000/redoc`

6. **Start the frontend (optional)**
   ```bash
   cd frontend
   python3 -m http.server 8080
   ```
   Access at: `http://127.0.0.1:8080/page.html`

## 📚 API Documentation

### Base URL
```
http://127.0.0.1:8000/api/v1
```

### 1. Instruments API

#### GET `/api/v1/instruments`

Fetch list of tradable instruments.

**Response:**
```json
[
  {
    "symbol": "AAPL",
    "name": "Apple Inc.",
    "exchange": "NASDAQ",
    "instrumentType": "EQUITY",
    "lastTradedPrice": 260.33,
    "change": 2.15,
    "changePercent": 0.83,
    "volume": 45000,
    "high": 262.50,
    "low": 258.20
  }
]
```

**Example:**
```bash
curl http://127.0.0.1:8000/api/v1/instruments
```

### 2. Order Management APIs

#### POST `/api/v1/orders`

Place a new order.

**Request Body:**
```json
{
  "symbol": "AAPL",
  "quantity": 10,
  "side": "BUY",
  "style": "MARKET"
}
```

**For LIMIT orders:**
```json
{
  "symbol": "TSLA",
  "quantity": 5,
  "side": "BUY",
  "style": "LIMIT",
  "price": 400.0
}
```

**Response:**
```json
{
  "orderId": "550e8400-e29b-41d4-a716-446655440000",
  "status": "EXECUTED",
  "message": "Order placed successfully"
}
```

**Example:**
```bash
# Market Order
curl -X POST http://127.0.0.1:8000/api/v1/orders \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "AAPL",
    "quantity": 10,
    "side": "BUY",
    "style": "MARKET"
  }'

# Limit Order
curl -X POST http://127.0.0.1:8000/api/v1/orders \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "TSLA",
    "quantity": 5,
    "side": "BUY",
    "style": "LIMIT",
    "price": 400.0
  }'
```

**Validations:**
- `quantity` must be > 0
- `side` must be "BUY" or "SELL"
- `style` must be "MARKET" or "LIMIT"
- `price` is required for LIMIT orders
- `price` must be > 0

**Order Statuses:**
- `NEW`: Order created
- `PLACED`: Order submitted to market
- `EXECUTED`: Order completed
- `CANCELLED`: Order cancelled

#### GET `/api/v1/orders/{orderId}`

Fetch order status by order ID.

**Response:**
```json
{
  "orderId": "550e8400-e29b-41d4-a716-446655440000",
  "symbol": "AAPL",
  "quantity": 10,
  "side": "BUY",
  "style": "MARKET",
  "price": null,
  "status": "EXECUTED",
  "createdAt": "2024-01-08T10:30:00",
  "executedPrice": 260.33,
  "executedAt": "2024-01-08T10:30:00.100"
}
```

**Example:**
```bash
curl http://127.0.0.1:8000/api/v1/orders/{orderId}
```

#### DELETE `/api/v1/orders/{orderId}`

Cancel a pending order.

**Response:**
```json
{
  "orderId": "550e8400-e29b-41d4-a716-446655440000",
  "status": "CANCELLED",
  "message": "Order cancelled successfully"
}
```

**Example:**
```bash
curl -X DELETE http://127.0.0.1:8000/api/v1/orders/{orderId}
```

### 3. Portfolio API

#### GET `/api/v1/portfolio`

Fetch current portfolio holdings.

**Response:**
```json
[
  {
    "symbol": "AAPL",
    "quantity": 10,
    "averagePrice": 260.33,
    "currentPrice": 262.48,
    "currentValue": 2624.80,
    "unrealizedPnl": 21.50,
    "change": 2.15,
    "changePercent": 0.83
  }
]
```

**Example:**
```bash
curl http://127.0.0.1:8000/api/v1/portfolio
```

### 4. Trades API

#### GET `/api/v1/trades`

Fetch list of executed trades.

**Response:**
```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "symbol": "AAPL",
    "qty": 10,
    "price": 260.33,
    "side": "BUY",
    "pnl": 0.0,
    "executedAt": "2024-01-08T10:30:00.100"
  }
]
```

**Example:**
```bash
curl http://127.0.0.1:8000/api/v1/trades
```

### 5. Statistics API

#### GET `/api/v1/stats`

Fetch trading statistics.

**Response:**
```json
{
  "total_pnl": 125.50
}
```

**Example:**
```bash
curl http://127.0.0.1:8000/api/v1/stats
```

## 💻 SDK Usage

The project includes a Python SDK wrapper for easier API interaction:

```python
from backend.sdk import BajajTradingSDK

# Initialize SDK
sdk = BajajTradingSDK(base_url="http://127.0.0.1:8000")

# Fetch instruments
instruments = sdk.get_instruments()
print(instruments)

# Place a MARKET order
order = sdk.place_order(
    symbol="AAPL",
    quantity=10,
    side="BUY",
    style="MARKET"
)
print(f"Order ID: {order['orderId']}")

# Place a LIMIT order
limit_order = sdk.place_order(
    symbol="TSLA",
    quantity=5,
    side="BUY",
    style="LIMIT",
    price=400.0
)

# Check order status
status = sdk.get_order_status(order['orderId'])
print(status)

# Get portfolio
portfolio = sdk.get_portfolio()
print(portfolio)

# Get trades
trades = sdk.get_trades()
print(trades)

# Cancel an order
sdk.cancel_order(order['orderId'])
```

## 🧪 Running Tests

Run unit tests using pytest:

```bash
cd backend
pytest tests/test_api.py -v
```

Or run all tests:

```bash
pytest tests/ -v
```

## 📁 Project Structure

```
TradeBajaj1/
├── backend/
│   ├── main.py              # FastAPI application and routes
│   ├── order_manager.py     # Order lifecycle management
│   ├── price_simulator.py   # Price simulation engine
│   ├── services.py          # Price fetching services
│   ├── sdk.py               # Python SDK wrapper
│   └── tests/
│       ├── test_api.py      # Unit tests for APIs
│       └── test_sdk.py      # SDK usage examples
├── frontend/
│   ├── page.html           # Trading dashboard UI
│   ├── script.js           # Frontend logic
│   └── style.css           # Styling
├── requirements.txt        # Python dependencies
└── README.md              # This file
```

## 🔍 Key Implementation Details

### Order Execution Simulation

- **MARKET Orders**: Execute immediately at current market price
- **LIMIT Orders**: Execute when price condition is met:
  - BUY LIMIT: Executes when current price ≤ limit price
  - SELL LIMIT: Executes when current price ≥ limit price

### Price Simulation

- Uses Geometric Brownian Motion for realistic price movements
- Different volatility levels per stock:
  - TSLA: 4% volatility (more volatile)
  - AAPL: 2% volatility
  - IBM: 1.5% volatility (less volatile)
- Prices update every 2-3 seconds

### Data Storage

- In-memory storage using Python dictionaries
- All data resets on server restart
- Suitable for simulation/demo purposes

### Error Handling

- Centralized exception handling
- Proper HTTP status codes:
  - `200`: Success
  - `201`: Created
  - `400`: Bad Request (validation errors)
  - `404`: Not Found
  - `422`: Unprocessable Entity (validation errors)
  - `500`: Internal Server Error

### Logging

- Comprehensive logging for all operations
- Logs order creation, execution, cancellations
- Error logging with stack traces
- Console output format: `TIMESTAMP - MODULE - LEVEL - MESSAGE`

## 📝 Assumptions Made

1. **Single User**: System designed for single hardcoded user (no authentication)
2. **In-Memory Storage**: All data stored in memory (resets on restart)
3. **Immediate Execution**: Market orders execute immediately
4. **Simplified Matching**: Limit orders execute immediately if condition met (simplified matching engine)
5. **Price Source**: Uses simulated prices (real API integration available but uses cache)
6. **No Commission**: Trading fees not included in calculations
7. **No Margin**: No margin trading or short selling implemented
8. **Fractional Shares**: Not supported (only whole numbers)
9. **Market Hours**: No market hours simulation (trading available 24/7)

## 🎯 API Endpoints Summary

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/instruments` | Get all tradable instruments |
| POST | `/api/v1/orders` | Place a new order |
| GET | `/api/v1/orders/{orderId}` | Get order status |
| DELETE | `/api/v1/orders/{orderId}` | Cancel an order |
| GET | `/api/v1/portfolio` | Get portfolio holdings |
| GET | `/api/v1/trades` | Get executed trades |
| GET | `/api/v1/stats` | Get trading statistics |

## 🚦 Sample API Workflow

1. **Fetch available instruments**
   ```bash
   curl http://127.0.0.1:8000/api/v1/instruments
   ```

2. **Place a BUY order**
   ```bash
   curl -X POST http://127.0.0.1:8000/api/v1/orders \
     -H "Content-Type: application/json" \
     -d '{"symbol":"AAPL","quantity":10,"side":"BUY","style":"MARKET"}'
   ```

3. **Check order status**
   ```bash
   curl http://127.0.0.1:8000/api/v1/orders/{orderId}
   ```

4. **View portfolio**
   ```bash
   curl http://127.0.0.1:8000/api/v1/portfolio
   ```

5. **View trades**
   ```bash
   curl http://127.0.0.1:8000/api/v1/trades
   ```

## 🔧 Development

### Adding New Instruments

Edit `backend/main.py` in the `get_instruments()` function:

```python
instruments = [
    {"symbol": "NEW", "name": "New Stock", "exchange": "NASDAQ", "instrumentType": "EQUITY"},
    # ... existing instruments
]
```

### Extending Order Types

Modify `backend/order_manager.py` to add new order types or execution logic.

## 📄 License

This project is created for educational/assessment purposes.

## 👨‍💻 Author

Created as part of a backend development assessment.

## 📞 Support

For issues or questions, please check the API documentation at `/docs` endpoint.
