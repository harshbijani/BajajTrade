from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict
import uuid
import logging
from datetime import datetime
from services import get_live_price, get_price_data
from contextlib import asynccontextmanager
import asyncio
from order_manager import OrderManager, OrderStatus, OrderType, OrderStyle

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize price simulator
    from price_simulator import simulator
    from services import get_real_price_from_api
    
    # Initialize with real prices
    for symbol in ["AAPL", "TSLA", "IBM"]:
        real_price = get_real_price_from_api(symbol)
        if real_price:
            simulator.initialize_from_api(symbol, real_price)
    
    logger.info("Application startup complete")
    yield
    logger.info("Application shutdown")
    # Shutdown (if needed)

app = FastAPI(
    title="Bajaj Trading API",
    description="Trading Platform API with order management and portfolio tracking",
    version="1.0.0",
    lifespan=lifespan
)

# Enable connection to your HTML file
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class OrderRequest(BaseModel):
    symbol: str = Field(..., description="Stock symbol (e.g., AAPL, TSLA)")
    quantity: int = Field(gt=0, description="Number of shares (must be > 0)")
    side: str = Field(..., description="Order side: BUY or SELL")
    style: str = Field(..., description="Order style: MARKET or LIMIT")
    price: Optional[float] = Field(None, gt=0, description="Price (required for LIMIT orders)")
    
    @validator('side')
    def validate_side(cls, v):
        if v.upper() not in ['BUY', 'SELL']:
            raise ValueError('side must be BUY or SELL')
        return v.upper()
    
    @validator('style')
    def validate_style(cls, v):
        if v.upper() not in ['MARKET', 'LIMIT']:
            raise ValueError('style must be MARKET or LIMIT')
        return v.upper()
    
    @validator('price')
    def validate_price(cls, v, values):
        if values.get('style', '').upper() == 'LIMIT' and v is None:
            raise ValueError('price is required for LIMIT orders')
        return v

# Global database
db = {
    "trades": [],
    "portfolio": {},
    "stats": {"total_pnl": 0.0},
    "orders": {}  # Store all orders with status tracking
}

# Initialize order manager
order_manager = OrderManager(db)

# Exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc: HTTPException):
    logger.error(f"HTTP Exception: {exc.status_code} - {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail, "status_code": exc.status_code}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc: Exception):
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "detail": str(exc)}
    )

@app.get("/api/v1/instruments", 
         summary="Fetch list of tradable instruments",
         description="Returns all available trading instruments with current prices and metadata",
         tags=["Instruments"])
def get_instruments():
    """
    Fetch list of tradable instruments
    
    Returns instruments with:
    - symbol: Stock ticker symbol
    - exchange: Stock exchange (NYSE, NASDAQ, etc.)
    - instrumentType: Type of instrument (EQUITY, ETF, etc.)
    - lastTradedPrice: Current/last traded price
    """
    logger.info("Fetching instruments")
    instruments = [
        {"symbol": "AAPL", "name": "Apple Inc.", "exchange": "NASDAQ", "instrumentType": "EQUITY"},
        {"symbol": "TSLA", "name": "Tesla Inc.", "exchange": "NASDAQ", "instrumentType": "EQUITY"},
        {"symbol": "IBM", "name": "International Business Machines", "exchange": "NYSE", "instrumentType": "EQUITY"}
    ]
    
    # Add current price data with all metrics
    for inst in instruments:
        price_data = get_price_data(inst["symbol"])
        inst["lastTradedPrice"] = price_data["price"]
        # Keep other price metrics for compatibility
        inst.update({k: v for k, v in price_data.items() if k != "price"})
    
    return instruments

@app.post("/api/v1/orders",
          summary="Place a new order",
          description="Place a BUY or SELL order (MARKET or LIMIT)",
          tags=["Orders"],
          status_code=status.HTTP_201_CREATED)
async def place_order(order: OrderRequest):
    """
    Place a new trading order
    
    - **MARKET orders**: Execute immediately at current market price
    - **LIMIT orders**: Execute when price reaches limit price (requires price field)
    """
    logger.info(f"Placing order: {order.side} {order.quantity} {order.symbol} @ {order.style}")
    
    # Validate symbol exists
    instruments_response = get_instruments()
    symbol_exists = any(inst["symbol"] == order.symbol for inst in instruments_response)
    if not symbol_exists:
        raise HTTPException(status_code=400, detail=f"Invalid symbol: {order.symbol}")
    
    # Create order with status NEW
    order_id = str(uuid.uuid4())
    new_order = order_manager.create_order(
        order_id=order_id,
        symbol=order.symbol,
        quantity=order.quantity,
        side=order.side,
        style=order.style,
        price=order.price
    )
    
    # Get current price
    current_price = get_live_price(order.symbol)
    
    # Execute order based on style
    if order.style == OrderStyle.MARKET.value:
        # Market orders execute immediately
        executed_order = await order_manager.execute_market_order(new_order, current_price)
        await process_executed_order(executed_order)
    else:
        # Limit orders - check if can execute immediately
        can_execute = order_manager.check_limit_execution(
            order.side, current_price, order.price
        )
        if can_execute:
            executed_order = await order_manager.execute_limit_order(
                new_order, current_price, order_manager.check_limit_execution
            )
            await process_executed_order(executed_order)
        else:
            # For simulation, we'll execute limit orders immediately if condition met
            # In real system, these would be queued for matching engine
            logger.info(f"Limit order {order_id} queued - waiting for price condition")
    
    return {
        "orderId": order_id,
        "status": new_order["status"],
        "message": "Order placed successfully"
    }

async def process_executed_order(order: Dict):
    """Process an executed order - update portfolio and trades"""
    if order["status"] != OrderStatus.EXECUTED.value:
        return
    
    executed_price = order["executedPrice"]
    symbol = order["symbol"]
    quantity = order["quantity"]
    side = order["side"]
    
    # Initialize portfolio entry if needed
    if symbol not in db["portfolio"]:
        db["portfolio"][symbol] = {"symbol": symbol, "quantity": 0, "avgPrice": 0.0}
    
    p = db["portfolio"][symbol]
    pnl = 0.0
    
    if side == OrderType.BUY.value:
        if p["quantity"] == 0:
            p["avgPrice"] = executed_price
        else:
            total_cost = (p["quantity"] * p["avgPrice"]) + (quantity * executed_price)
            p["avgPrice"] = total_cost / (p["quantity"] + quantity)
        p["quantity"] += quantity
        logger.info(f"Portfolio updated: Bought {quantity} {symbol} @ ${executed_price}")
    else:
        if p["quantity"] < quantity:
            order["status"] = OrderStatus.CANCELLED.value
            raise HTTPException(status_code=400, detail="Insufficient shares")
        # Realized P&L = (Sell Price - Buy Price) * Quantity
        pnl = (executed_price - p["avgPrice"]) * quantity
        db["stats"]["total_pnl"] += pnl
        p["quantity"] -= quantity
        # Clean up if no shares left
        if p["quantity"] == 0:
            p["avgPrice"] = 0.0
        logger.info(f"Portfolio updated: Sold {quantity} {symbol} @ ${executed_price} (P&L: ${pnl:.2f})")
    
    # Add to trade history
    db["trades"].insert(0, {
        "id": order["orderId"],
        "symbol": symbol,
        "qty": quantity,
        "price": executed_price,
        "side": side,
        "pnl": round(pnl, 2),
        "executedAt": order["executedAt"]
    })

@app.get("/api/v1/orders/{order_id}",
         summary="Fetch order status",
         description="Get status and details of a specific order",
         tags=["Orders"])
def get_order_status(order_id: str):
    """
    Fetch order status by order ID
    
    Returns order details including:
    - orderId: Unique order identifier
    - status: Order status (NEW, PLACED, EXECUTED, CANCELLED)
    - symbol, quantity, side, style
    - executedPrice: Price at which order was executed (if executed)
    - createdAt, executedAt: Timestamps
    """
    logger.info(f"Fetching order status: {order_id}")
    order = order_manager.get_order(order_id)
    
    if not order:
        raise HTTPException(status_code=404, detail=f"Order not found: {order_id}")
    
    return order

@app.delete("/api/v1/orders/{order_id}",
           summary="Cancel an order",
           description="Cancel a pending order (only if not executed)",
           tags=["Orders"])
def cancel_order(order_id: str):
    """Cancel an order if it hasn't been executed"""
    logger.info(f"Cancelling order: {order_id}")
    order = order_manager.cancel_order(order_id)
    
    if not order:
        raise HTTPException(status_code=404, detail=f"Order not found or cannot be cancelled: {order_id}")
    
    return {"orderId": order_id, "status": order["status"], "message": "Order cancelled successfully"}

@app.get("/api/v1/portfolio",
         summary="Fetch portfolio holdings",
         description="Get current portfolio with all holdings",
         tags=["Portfolio"])
def get_portfolio():
    """
    Fetch current portfolio holdings
    
    Returns portfolio with fields:
    - symbol: Stock symbol
    - quantity: Number of shares held
    - averagePrice: Average purchase price
    - currentValue: Current market value (quantity * currentPrice)
    """
    logger.info("Fetching portfolio")
    portfolio_items = []
    for v in db["portfolio"].values():
        if v["quantity"] > 0:
            price_data = get_price_data(v["symbol"])
            current_price = price_data["price"]
            current_value = v["quantity"] * current_price
            unrealized_pnl = (current_price - v["avgPrice"]) * v["quantity"]
            portfolio_items.append({
                "symbol": v["symbol"],
                "quantity": v["quantity"],
                "averagePrice": round(v["avgPrice"], 2),
                "currentPrice": round(current_price, 2),
                "currentValue": round(current_value, 2),
                "unrealizedPnl": round(unrealized_pnl, 2),
                "change": price_data["change"],
                "changePercent": price_data["changePercent"]
            })
    return portfolio_items

@app.get("/api/v1/trades",
         summary="Fetch executed trades",
         description="Get list of all executed trades",
         tags=["Trades"])
def get_trades():
    """Fetch list of executed trades for the user"""
    logger.info(f"Fetching trades (count: {len(db['trades'])})")
    return db["trades"]

@app.get("/api/v1/stats",
         summary="Fetch trading statistics",
         description="Get overall trading statistics and P&L",
         tags=["Statistics"])
def get_stats():
    """Fetch trading statistics including total P&L"""
    return db["stats"]
