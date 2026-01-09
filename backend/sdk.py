import requests

class BajajTradingSDK:
    def __init__(self, base_url="http://127.0.0.1:8000"):
        self.base_url = base_url

    def get_instruments(self):
        """Fetch list of tradable instruments"""
        response = requests.get(f"{self.base_url}/api/v1/instruments")
        return response.json()

    def place_order(self, symbol, quantity, side, style, price=None):
        """Place a BUY or SELL order"""
        payload = {
            "symbol": symbol,
            "quantity": quantity,
            "side": side,
            "style": style,
            "price": price
        }
        response = requests.post(f"{self.base_url}/api/v1/orders", json=payload)
        return response.json()

    def get_order_status(self, order_id):
        """Check status of a specific order"""
        response = requests.get(f"{self.base_url}/api/v1/orders/{order_id}")
        return response.json()

    def get_trades(self):
        """Fetch list of executed trades"""
        response = requests.get(f"{self.base_url}/api/v1/trades")
        return response.json()

    def get_portfolio(self):
        """Fetch current portfolio holdings"""
        response = requests.get(f"{self.base_url}/api/v1/portfolio")
        return response.json()
    
    def cancel_order(self, order_id):
        """Cancel a pending order"""
        response = requests.delete(f"{self.base_url}/api/v1/orders/{order_id}")
        response.raise_for_status()
        return response.json()
