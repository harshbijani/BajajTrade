"""
Order Management Module
Handles order lifecycle and execution simulation
"""
import asyncio
import logging
from datetime import datetime
from typing import Dict, Optional
from enum import Enum

logger = logging.getLogger(__name__)

class OrderStatus(Enum):
    NEW = "NEW"
    PLACED = "PLACED"
    EXECUTED = "EXECUTED"
    CANCELLED = "CANCELLED"

class OrderType(Enum):
    BUY = "BUY"
    SELL = "SELL"

class OrderStyle(Enum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"

class OrderManager:
    """Manages order lifecycle and execution"""
    
    def __init__(self, db: Dict):
        self.db = db
        self.execution_tasks = {}
        logger.info("OrderManager initialized")
    
    def create_order(self, order_id: str, symbol: str, quantity: int, 
                    side: str, style: str, price: Optional[float] = None) -> Dict:
        """Create a new order with status NEW"""
        order = {
            "orderId": order_id,
            "symbol": symbol,
            "quantity": quantity,
            "side": side.upper(),
            "style": style.upper(),
            "price": price,
            "status": OrderStatus.NEW.value,
            "createdAt": datetime.now().isoformat(),
            "executedPrice": None,
            "executedAt": None
        }
        
        self.db["orders"][order_id] = order
        logger.info(f"Order created: {order_id} - {side} {quantity} {symbol} @ {style}")
        return order
    
    async def execute_market_order(self, order: Dict, current_price: float) -> Dict:
        """Execute a market order immediately"""
        order_id = order["orderId"]
        order["status"] = OrderStatus.PLACED.value
        await asyncio.sleep(0.1)  # Simulate brief processing delay
        
        order["status"] = OrderStatus.EXECUTED.value
        order["executedPrice"] = round(current_price, 2)
        order["executedAt"] = datetime.now().isoformat()
        
        logger.info(f"Market order executed: {order_id} at ${current_price}")
        return order
    
    async def execute_limit_order(self, order: Dict, current_price: float, 
                                 check_execution: callable) -> Dict:
        """Execute a limit order when price condition is met"""
        order_id = order["orderId"]
        order["status"] = OrderStatus.PLACED.value
        limit_price = order["price"]
        side = order["side"]
        
        # Check if limit order can be executed
        if check_execution(side, current_price, limit_price):
            order["status"] = OrderStatus.EXECUTED.value
            order["executedPrice"] = round(limit_price, 2)
            order["executedAt"] = datetime.now().isoformat()
            logger.info(f"Limit order executed: {order_id} at ${limit_price}")
        else:
            # For simulation, if limit not met immediately, we'll check in background
            # In real system, this would be handled by order matching engine
            logger.info(f"Limit order pending: {order_id} - {side} @ ${limit_price} (current: ${current_price})")
        
        return order
    
    def cancel_order(self, order_id: str) -> Optional[Dict]:
        """Cancel an order"""
        if order_id not in self.db["orders"]:
            return None
        
        order = self.db["orders"][order_id]
        if order["status"] in [OrderStatus.EXECUTED.value, OrderStatus.CANCELLED.value]:
            logger.warning(f"Cannot cancel order {order_id} - status: {order['status']}")
            return None
        
        order["status"] = OrderStatus.CANCELLED.value
        logger.info(f"Order cancelled: {order_id}")
        return order
    
    def get_order(self, order_id: str) -> Optional[Dict]:
        """Get order by ID"""
        return self.db["orders"].get(order_id)
    
    def check_limit_execution(self, side: str, current_price: float, limit_price: float) -> bool:
        """Check if limit order execution condition is met"""
        if side == OrderType.BUY.value:
            # Buy limit: execute if current price <= limit price
            return current_price <= limit_price
        else:  # SELL
            # Sell limit: execute if current price >= limit price
            return current_price >= limit_price
