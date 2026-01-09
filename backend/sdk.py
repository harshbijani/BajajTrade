import requests
import time
from price_simulator import simulator

ALPHA_VANTAGE_KEY = "D14S5L65LKDWKF04"
BASE_URL = "https://www.alphavantage.co/query"

# Simple cache to save API calls
price_cache = {}
CACHE_EXPIRY = 60  # Refresh every 1 minute

def get_real_price_from_api(symbol: str):
    """Get real price from Alpha Vantage API (for initialization)"""
    symbol = symbol.upper()
    current_time = time.time()

    if symbol in price_cache:
        data = price_cache[symbol]
        if current_time - data["timestamp"] < CACHE_EXPIRY:
            return data["price"]

    params = {"function": "GLOBAL_QUOTE", "symbol": symbol, "apikey": ALPHA_VANTAGE_KEY}
    
    try:
        response = requests.get(BASE_URL, params=params)
        data = response.json()
        
        if "Note" in data: return None # API limit reached
            
        quote = data.get("Global Quote", {})
        price_str = quote.get("05. price")
        
        if price_str:
            price = float(price_str)
            price_cache[symbol] = {"price": price, "timestamp": current_time}
            return price
        return None
    except:
        return None

def get_live_price(symbol: str):
    """Get simulated live price with fluctuations"""
    symbol = symbol.upper()
    
    # Try to get real price occasionally for initialization
    real_price = get_real_price_from_api(symbol)
    if real_price:
        simulator.initialize_from_api(symbol, real_price)
    
    # Update and return simulated price
    price_data = simulator.update_price(symbol)
    if price_data:
        return price_data["price"]
    
    # Fallback
    return 150.0

def get_price_data(symbol: str):
    """Get full price data with all metrics"""
    symbol = symbol.upper()
    
    # Try to sync with real API occasionally
    real_price = get_real_price_from_api(symbol)
    if real_price:
        simulator.initialize_from_api(symbol, real_price)
    
    # Get simulated price data
    price_data = simulator.update_price(symbol)
    if price_data:
        return price_data
    
    # Fallback
    return {
        "price": 150.0,
        "change": 0.0,
        "changePercent": 0.0,
        "volume": 5000,
        "high": 150.0,
        "low": 150.0,
        "bid": 149.9,
        "ask": 150.1,
        "priceHistory": [150.0]
    }
