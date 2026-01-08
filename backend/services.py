import requests
import time

# --- CONFIGURATION ---
ALPHA_VANTAGE_KEY = "D14S5L65LKDWKF04"
BASE_URL = "https://www.alphavantage.co/query"

# Simple cache: { "SYMBOL": {"price": 150.0, "timestamp": 1672531200} }
price_cache = {}
CACHE_EXPIRY = 300  # 5 minutes in seconds

def get_live_price(symbol: str):
    symbol = symbol.upper()
    current_time = time.time()

    # 1. Check if we have a fresh cached price
    if symbol in price_cache:
        data = price_cache[symbol]
        if current_time - data["timestamp"] < CACHE_EXPIRY:
            print(f"Using cached price for {symbol}")
            return data["price"]

    # 2. If not cached, call Alpha Vantage
    params = {
        "function": "GLOBAL_QUOTE",
        "symbol": symbol,
        "apikey": ALPHA_VANTAGE_KEY
    }
    
    try:
        response = requests.get(BASE_URL, params=params)
        data = response.json()
        
        # Check for API Limit/Error messages
        if "Note" in data:
            print("API Limit Reached (25/day). Please wait.")
            return None
            
        quote = data.get("Global Quote", {})
        price_str = quote.get("05. price") # Alpha Vantage key format
        
        if price_str:
            price = float(price_str)
            # Update Cache
            price_cache[symbol] = {"price": price, "timestamp": current_time}
            return price
        
        return None
    except Exception as e:
        print(f"Error fetching {symbol}: {e}")
        return None