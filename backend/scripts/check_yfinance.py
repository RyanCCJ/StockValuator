
import yfinance as yf
import json
import pandas as pd
from datetime import datetime

def check_full_yfinance_data(symbol):
    print(f"\n{'='*50}")
    print(f"🔎 Analyzing yfinance data for: {symbol}")
    print(f"{'='*50}\n")
    
    try:
        ticker = yf.Ticker(symbol)
        
        # 1. Info Dictionary (Most comprehensive source)
        print("📊 [ticker.info] (Key Metrics & Metadata)")
        info = ticker.info
        if info:
            sorted_keys = sorted(info.keys())
            # Print in groups for readability
            print(f"Total keys: {len(sorted_keys)}")
            print("\nSample Data (First 20 keys):")
            for k in sorted_keys[:20]:
                val = info[k]
                if isinstance(val, (str, int, float, bool)) or val is None:
                     print(f"  - {k}: {val}")
                else:
                     print(f"  - {k}: {type(val)}")
            
            # Specific check for commonly requested fields
            print("\n📌 Targeted Fields Check:")
            targets = [
                'symbol', 'longName', 'sector', 'industry', 
                'marketCap', 'trailingPE', 'forwardPE', 'dividendYield', 
                'trailingEps', 'forwardEps', 'beta', 
                'fiftyTwoWeekHigh', 'fiftyTwoWeekLow',
                'payoutRatio', 'profitMargins', 'revenueGrowth'
            ]
            for t in targets:
                print(f"  - {t}: {info.get(t, 'N/A')}")
        else:
            print("⚠️ ticker.info is empty or failed")

        # 2. Holders (Stock style)
        print("\n👥 [ticker.major_holders] (Stocks)")
        try:
            mh = ticker.major_holders
            if mh is not None and not mh.empty:
                print(mh)
            else:
                print("No major_holders found")
        except Exception as e:
            print(f"Error: {e}")

        print("\n🏛 [ticker.institutional_holders] (Stocks)")
        try:
            ih = ticker.institutional_holders
            if ih is not None and not ih.empty:
                print(ih.head())
            else:
                print("No institutional_holders found")
        except Exception as e:
            print(f"Error: {e}")

        # 3. ETF Specifics
        print("\n🧺 [ETF Specifics]")
        
        print("  - ticker.funds_data:")
        try:
            if hasattr(ticker, "funds_data") and ticker.funds_data:
                fd = ticker.funds_data
                print(f"    Description: {fd.description[:100]}...")
                
                print("\n    Top Holdings:")
                if fd.top_holdings is not None and not fd.top_holdings.empty:
                    print(fd.top_holdings.head())
                else:
                    print("    No top_holdings found")
                    
                print("\n    Sector Weightings:")
                if fd.sector_weightings:
                    print(fd.sector_weightings)
                else:
                    print("    No sector_weightings found")
            else:
                print("    ticker.funds_data is None/Empty")
        except Exception as e:
            print(f"    Error access funds_data: {e}")

    except Exception as e:
        print(f"\n❌ Critical Error fetching ticker: {e}")

if __name__ == "__main__":
    symbol = input("Enter symbol to analyze (default: AAPL): ").strip().upper()
    if not symbol:
        symbol = "AAPL"
    check_full_yfinance_data(symbol)
