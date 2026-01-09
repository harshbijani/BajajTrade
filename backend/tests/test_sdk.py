from backend.sdk import BajajTradingSDK
import time

# Initialize our custom SDK
sdk = BajajTradingSDK(base_url="http://127.0.0.1:8000")

print("--- 1. Fetching Instruments ---")
print(sdk.get_instruments())

print("\n--- 2. Placing a Paper Trade via SDK ---")
order = sdk.place_order(symbol="IBM", quantity=10, side="BUY", style="MARKET")
print(f"Order Executed: {order}")

print("\n--- 3. Checking Portfolio ---")
time.sleep(1) # Give the backend a second to process
print(sdk.get_portfolio())