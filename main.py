from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field
from typing import List, Optional
import uuid
from services import get_live_price

app = FastAPI(title="Bajaj Paper Trading Backend")

# --- DATA MODELS ---
class OrderRequest(BaseModel):
    symbol: str
    quantity: int = Field(gt=0)
    side: str  # BUY or SELL
    style: str # MARKET or LIMIT
    price: Optional[float] = None

# --- IN-MEMORY DATABASE ---
db = {
    "orders": {},
    "trades": [],
    "portfolio": {}
}

# --- HELPERS ---
def process_trade(order_id, symbol, qty, side, price):
    # 1. Record Trade
    trade = {"id": str(uuid.uuid4())[:8], "symbol": symbol, "qty": qty, "price": price, "side": side}
    db["trades"].append(trade)

    # 2. Update Portfolio
    if symbol not in db["portfolio"]:
        db["portfolio"][symbol] = {"symbol": symbol, "quantity": 0, "avgPrice": 0.0}
    
    p = db["portfolio"][symbol]
    if side == "BUY":
        total_cost = (p["quantity"] * p["avgPrice"]) + (qty * price)
        p["quantity"] += qty
        p["avgPrice"] = total_cost / p["quantity"]
    else:
        p["quantity"] = max(0, p["quantity"] - qty)

# --- ROUTES ---
@app.get("/api/v1/instruments")
def list_common_stocks():
    # Mocked list of popular stocks for the simulator
    return [{"symbol": "AAPL", "name": "Apple"}, {"symbol": "TSLA", "name": "Tesla"}, {"symbol": "IBM", "name": "IBM"}]

@app.post("/api/v1/orders", status_code=201)
def place_order(order: OrderRequest):
    # Fetch real price from Alpha Vantage
    market_price = get_live_price(order.symbol)
    if market_price is None:
        raise HTTPException(status_code=400, detail="Price unavailable. API limit may be reached.")

    # Validation
    if order.style == "LIMIT" and not order.price:
        raise HTTPException(status_code=400, detail="Limit price required")

    execution_price = market_price if order.style == "MARKET" else order.price
    order_id = str(uuid.uuid4())[:12]
    
    # Execute paper trade immediately
    process_trade(order_id, order.symbol, order.quantity, order.side, execution_price)

    order_record = {**order.dict(), "id": order_id, "status": "EXECUTED", "price": execution_price}
    db["orders"][order_id] = order_record
    return order_record

@app.get("/api/v1/portfolio")
def get_portfolio():
    return [v for v in db["portfolio"].values() if v["quantity"] > 0]

@app.get("/api/v1/trades")
def get_trades():
    return db["trades"]

