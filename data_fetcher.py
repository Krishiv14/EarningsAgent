"""
Data Fetcher Module - FIXED VERSION
Fetches fundamental financial data for Indian stocks using yfinance
"""

import time
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import streamlit as st

# Small delay between Yahoo API calls to reduce 429 (Too Many Requests)
_YAHOO_DELAY_SEC = 0.6


def _is_rate_limited(e: Exception) -> bool:
    """Check if the exception is Yahoo rate-limiting (HTTP 429)."""
    msg = str(e).lower()
    if "429" in msg or "too many requests" in msg:
        return True
    resp = getattr(e, "response", None)
    return resp is not None and getattr(resp, "status_code", None) == 429


class IndianStockDataFetcher:
    """Fetch financial data for NSE/BSE listed companies"""
    
    def __init__(self, ticker: str):
        """
        Initialize with ticker symbol
        Args:
            ticker: Stock symbol (e.g., 'RELIANCE', 'TCS', 'INFY')
        """
        # Add .NS suffix for NSE stocks if not present
        if not ticker.endswith('.NS') and not ticker.endswith('.BO'):
            self.ticker = f"{ticker}.NS"
        else:
            self.ticker = ticker
            
        try:
            self.stock = yf.Ticker(self.ticker)
        except Exception as e:
            st.error(f"Error initializing ticker {self.ticker}: {e}")
            self.stock = None
        
    def get_company_info(self):
        """Get basic company information"""
        if not self.stock:
            return None
            
        try:
            # Try to get info with timeout
            info = self.stock.info
            
            # Check if info is valid (not empty)
            if not info or len(info) == 0:
                st.error(f"No data available for {self.ticker}")
                return None
            
            # Check if it's a valid stock (has a name)
            if 'longName' not in info and 'shortName' not in info:
                st.error(f"Invalid ticker: {self.ticker}")
                return None
            
            return {
                'name': info.get('longName') or info.get('shortName', 'N/A'),
                'sector': info.get('sector', 'N/A'),
                'industry': info.get('industry', 'N/A'),
                'market_cap': info.get('marketCap', 0),
                'website': info.get('website', 'N/A'),
                'description': info.get('longBusinessSummary', 'N/A')
            }
        except KeyError as e:
            st.error(f"Data format error for {self.ticker}: {e}")
            return None
        except Exception as e:
            if _is_rate_limited(e):
                st.error("Yahoo Finance is rate-limiting (too many requests). Please wait 1–2 minutes and try again.")
            else:
                st.error(f"Error fetching company info: {str(e)}")
            return None
    
    def get_financial_metrics(self):
        """Get key financial metrics"""
        if not self.stock:
            return None
            
        try:
            info = self.stock.info
            
            if not info:
                return None
            
            return {
                'current_price': info.get('currentPrice') or info.get('regularMarketPrice', 0),
                'pe_ratio': info.get('trailingPE', 0),
                'pb_ratio': info.get('priceToBook', 0),
                'debt_to_equity': info.get('debtToEquity', 0),
                'roe': info.get('returnOnEquity', 0),
                'profit_margin': info.get('profitMargins', 0),
                'revenue_growth': info.get('revenueGrowth', 0),
                'earnings_growth': info.get('earningsGrowth', 0)
            }
        except Exception as e:
            if _is_rate_limited(e):
                st.error("Yahoo Finance is rate-limiting (too many requests). Please wait 1–2 minutes and try again.")
            else:
                st.warning(f"Error fetching metrics: {e}")
            return None
    
    def get_quarterly_financials(self):
        """Get quarterly financial statements"""
        if not self.stock:
            return None
            
        try:
            # Get quarterly financials
            quarterly_income = self.stock.quarterly_financials
            quarterly_balance = self.stock.quarterly_balance_sheet
            quarterly_cashflow = self.stock.quarterly_cashflow
            
            return {
                'income_statement': quarterly_income,
                'balance_sheet': quarterly_balance,
                'cashflow': quarterly_cashflow
            }
        except Exception as e:
            if _is_rate_limited(e):
                st.error("Yahoo Finance is rate-limiting (too many requests). Please wait 1–2 minutes and try again.")
            else:
                st.warning(f"Error fetching quarterly data: {e}")
            return None
    
    def calculate_delta_analysis(self):
        """
        Calculate delta between Revenue and Profit
        This is the key insight: When revenue rises but profit falls, WHY?
        """
        if not self.stock:
            return None
            
        try:
            quarterly = self.stock.quarterly_financials
            
            if quarterly is None or quarterly.empty:
                return None
            
            # Get latest two quarters
            if len(quarterly.columns) < 2:
                st.info("Not enough quarterly data for delta analysis")
                return None
                
            quarters = quarterly.columns[:2]
            
            # Extract revenue and net income
            revenue_row = None
            profit_row = None
            
            # Try different possible row names
            revenue_names = ['Total Revenue', 'Revenue', 'Total Revenues', 'Operating Revenue']
            profit_names = ['Net Income', 'Net Income Common Stockholders', 
                          'Net Income Applicable To Common Shares', 'Normalized Income']
            
            for name in revenue_names:
                if name in quarterly.index:
                    revenue_row = name
                    break
                    
            for name in profit_names:
                if name in quarterly.index:
                    profit_row = name
                    break
            
            if not revenue_row or not profit_row:
                st.info("Could not find revenue/profit data in quarterly financials")
                return None
            
            latest_revenue = quarterly.loc[revenue_row, quarters[0]]
            prev_revenue = quarterly.loc[revenue_row, quarters[1]]
            latest_profit = quarterly.loc[profit_row, quarters[0]]
            prev_profit = quarterly.loc[profit_row, quarters[1]]
            
            # Handle zero values
            if prev_revenue == 0 or prev_profit == 0:
                return None
            
            revenue_change = ((latest_revenue - prev_revenue) / abs(prev_revenue)) * 100
            profit_change = ((latest_profit - prev_profit) / abs(prev_profit)) * 100
            
            # Delta Detection
            delta_detected = False
            delta_type = "Normal"
            
            if revenue_change > 0 and profit_change < 0:
                delta_detected = True
                delta_type = "Revenue Up, Profit Down ⚠️"
            elif revenue_change < 0 and profit_change > 0:
                delta_detected = True
                delta_type = "Revenue Down, Profit Up 🤔"
            
            return {
                'latest_quarter': quarters[0].strftime('%Y-%m-%d') if hasattr(quarters[0], 'strftime') else str(quarters[0]),
                'previous_quarter': quarters[1].strftime('%Y-%m-%d') if hasattr(quarters[1], 'strftime') else str(quarters[1]),
                'revenue_change_pct': round(float(revenue_change), 2),
                'profit_change_pct': round(float(profit_change), 2),
                'delta_detected': delta_detected,
                'delta_type': delta_type,
                'latest_revenue': float(latest_revenue),
                'latest_profit': float(latest_profit)
            }
            
        except Exception as e:
            if _is_rate_limited(e):
                st.error("Yahoo Finance is rate-limiting (too many requests). Please wait 1–2 minutes and try again.")
            else:
                st.warning(f"Error in delta analysis: {e}")
            return None
    
    def get_historical_price(self, period='1y'):
        """Get historical stock price data"""
        if not self.stock:
            return None
            
        try:
            hist = self.stock.history(period=period)
            
            if hist is None or hist.empty:
                st.warning(f"No price history available for {self.ticker}")
                return None
                
            return hist
        except Exception as e:
            if _is_rate_limited(e):
                st.error("Yahoo Finance is rate-limiting (too many requests). Please wait 1–2 minutes and try again.")
            else:
                st.warning(f"Error fetching price history: {e}")
            return None


# Utility function for easy access
def fetch_stock_data(ticker: str):
    """
    Quick function to fetch all relevant data for a ticker.
    Adds short delays between Yahoo calls to reduce 429 rate-limit errors.
    """
    fetcher = IndianStockDataFetcher(ticker)
    time.sleep(_YAHOO_DELAY_SEC)
    info = fetcher.get_company_info()
    time.sleep(_YAHOO_DELAY_SEC)
    metrics = fetcher.get_financial_metrics()
    time.sleep(_YAHOO_DELAY_SEC)
    quarterly = fetcher.get_quarterly_financials()
    time.sleep(_YAHOO_DELAY_SEC)
    delta = fetcher.calculate_delta_analysis()
    time.sleep(_YAHOO_DELAY_SEC)
    price_history = fetcher.get_historical_price()

    return {
        'info': info,
        'metrics': metrics,
        'quarterly': quarterly,
        'delta': delta,
        'price_history': price_history,
    }