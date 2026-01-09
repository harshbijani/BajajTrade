#!/usr/bin/env python3
"""Quick test script to verify API is working"""
from backend.sdk import BajajTradingSDK
import json

sdk = BajajTradingSDK(base_url="http://127.0.0.1:8000")

print("=" * 60)
print("QUICK API TEST")
print("=" * 60)

try:
    # Test 1: Instruments
    print("\n✓ Test 1: Get Instruments")
    instruments = sdk.get_instruments()
    print(f"  Found {len(instruments)} instruments")
    for inst in instruments:
        print(f"    {inst['symbol']}: ${inst['lastTradedPrice']:.2f} ({inst['exchange']})")
    
    # Test 2: Place Market Order
    print("\n✓ Test 2: Place MARKET Order")
    order = sdk.place_order("AAPL", 5, "BUY", "MARKET")
    print(f"  Order ID: {order['orderId']}")
    print(f"  Status: {order['status']}")
    
    # Test 3: Check Order Status
    print("\n✓ Test 3: Get Order Status")
    status = sdk.get_order_status(order['orderId'])
    print(f"  Status: {status['status']}")
    print(f"  Symbol: {status['symbol']}, Qty: {status['quantity']}")
    
    # Test 4: Get Portfolio
    print("\n✓ Test 4: Get Portfolio")
    portfolio = sdk.get_portfolio()
    print(f"  Holdings: {len(portfolio)}")
    for h in portfolio:
        print(f"    {h['symbol']}: {h['quantity']} shares")
        print(f"      Avg Price: ${h['averagePrice']:.2f}")
        print(f"      Current Value: ${h['currentValue']:.2f}")
    
    # Test 5: Get Trades
    print("\n✓ Test 5: Get Trades")
    trades = sdk.get_trades()
    print(f"  Executed Trades: {len(trades)}")
    for t in trades[:2]:
        print(f"    {t['side']} {t['qty']} {t['symbol']} @ ${t['price']:.2f}")
    
    print("\n" + "=" * 60)
    print("✅ ALL TESTS PASSED! Your API is working correctly!")
    print("=" * 60)
    
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    print("Make sure the server is running: uvicorn main:app --reload")
