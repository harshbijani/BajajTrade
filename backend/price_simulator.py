import random
import time
import math
from typing import Dict

class PriceSimulator:
    """
    Simulates realistic stock price movements using geometric Brownian motion
    """
    def __init__(self):
        # Base prices (starting from real API prices)
        self.base_prices: Dict[str, float] = {
            "AAPL": 260.0,
            "TSLA": 430.0,
            "IBM": 295.0
        }
        # Current simulated prices
        self.current_prices: Dict[str, float] = self.base_prices.copy()
        # Price history for each symbol (last 100 points)
        self.price_history: Dict[str, list] = {symbol: [price] for symbol, price in self.base_prices.items()}
        # Volatility settings (higher = more volatile)
        self.volatility: Dict[str, float] = {
            "AAPL": 0.02,  # 2% volatility
            "TSLA": 0.04,  # 4% volatility (more volatile)
            "IBM": 0.015   # 1.5% volatility (less volatile)
        }
        # Volume simulation
        self.volumes: Dict[str, int] = {symbol: random.randint(1000, 10000) for symbol in self.base_prices.keys()}
        # Last update time
        self.last_update: Dict[str, float] = {symbol: time.time() for symbol in self.base_prices.keys()}
        
    def initialize_from_api(self, symbol: str, real_price: float):
        """Initialize simulator with real API price"""
        if symbol not in self.current_prices:
            self.base_prices[symbol] = real_price
            self.current_prices[symbol] = real_price
            self.price_history[symbol] = [real_price]
            self.volatility[symbol] = 0.02
            self.volumes[symbol] = random.randint(1000, 10000)
            self.last_update[symbol] = time.time()
        else:
            # Occasionally sync with real price to keep it realistic
            if random.random() < 0.1:  # 10% chance to sync
                self.base_prices[symbol] = real_price
                self.current_prices[symbol] = real_price
    
    def update_price(self, symbol: str) -> Dict:
        """
        Update price using geometric Brownian motion (realistic stock movement)
        Returns dict with price, change, changePercent, volume, etc.
        """
        if symbol not in self.current_prices:
            return None
            
        current_price = self.current_prices[symbol]
        volatility = self.volatility[symbol]
        
        # Geometric Brownian Motion: dS = S * (mu * dt + sigma * dW)
        # Simplified: price_change = current_price * (drift + random_shock)
        
        # Drift (slight upward bias, can be negative)
        drift = random.uniform(-0.0001, 0.0003)  # Small drift
        
        # Random shock (volatility component)
        random_shock = random.gauss(0, volatility)  # Normal distribution
        
        # Calculate new price
        price_change_percent = drift + random_shock
        new_price = current_price * (1 + price_change_percent)
        
        # Ensure price doesn't go negative or too extreme
        new_price = max(new_price, current_price * 0.5)  # Max 50% drop
        new_price = min(new_price, current_price * 1.5)  # Max 50% gain
        
        # Calculate change
        price_change = new_price - current_price
        change_percent = (price_change / current_price) * 100
        
        # Update current price
        self.current_prices[symbol] = new_price
        
        # Update price history (keep last 100 points)
        self.price_history[symbol].append(new_price)
        if len(self.price_history[symbol]) > 100:
            self.price_history[symbol].pop(0)
        
        # Simulate volume (higher volume on bigger moves)
        volume_multiplier = 1 + abs(change_percent) / 10
        base_volume = self.volumes[symbol]
        volume = int(base_volume * random.uniform(0.7, 1.3) * volume_multiplier)
        self.volumes[symbol] = volume
        
        # Calculate high/low for the session
        session_high = max(self.price_history[symbol][-20:]) if len(self.price_history[symbol]) > 1 else new_price
        session_low = min(self.price_history[symbol][-20:]) if len(self.price_history[symbol]) > 1 else new_price
        
        # Bid/Ask spread (typically 0.1-0.5% of price)
        spread_percent = random.uniform(0.001, 0.005)
        bid = new_price * (1 - spread_percent / 2)
        ask = new_price * (1 + spread_percent / 2)
        
        return {
            "price": round(new_price, 2),
            "change": round(price_change, 2),
            "changePercent": round(change_percent, 2),
            "volume": volume,
            "high": round(session_high, 2),
            "low": round(session_low, 2),
            "bid": round(bid, 2),
            "ask": round(ask, 2),
            "priceHistory": self.price_history[symbol][-20:]  # Last 20 points for chart
        }
    
    def get_price_data(self, symbol: str) -> Dict:
        """Get current price data with all metrics"""
        if symbol not in self.current_prices:
            return None
        
        current_price = self.current_prices[symbol]
        base_price = self.base_prices[symbol]
        total_change = current_price - base_price
        total_change_percent = (total_change / base_price) * 100
        
        session_high = max(self.price_history[symbol]) if len(self.price_history[symbol]) > 1 else current_price
        session_low = min(self.price_history[symbol]) if len(self.price_history[symbol]) > 1 else current_price
        
        spread_percent = random.uniform(0.001, 0.005)
        bid = current_price * (1 - spread_percent / 2)
        ask = current_price * (1 + spread_percent / 2)
        
        return {
            "price": round(current_price, 2),
            "change": round(total_change, 2),
            "changePercent": round(total_change_percent, 2),
            "volume": self.volumes[symbol],
            "high": round(session_high, 2),
            "low": round(session_low, 2),
            "bid": round(bid, 2),
            "ask": round(ask, 2),
            "priceHistory": self.price_history[symbol][-20:]
        }

# Global simulator instance
simulator = PriceSimulator()
