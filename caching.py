"""
Caching Module
Implements smart caching to improve performance
"""

import streamlit as st
import pickle
import os
from datetime import datetime, timedelta
from typing import Any, Optional
import hashlib


class CacheManager:
    """
    Manages caching of expensive operations
    """
    
    def __init__(self, cache_dir='data/cache'):
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)
    
    def _get_cache_key(self, prefix: str, identifier: str) -> str:
        """Generate cache key"""
        # Create hash of identifier for consistent file names
        id_hash = hashlib.md5(identifier.encode()).hexdigest()[:8]
        return f"{prefix}_{id_hash}"
    
    def _get_cache_path(self, cache_key: str) -> str:
        """Get full path to cache file"""
        return os.path.join(self.cache_dir, f"{cache_key}.pkl")
    
    def get(self, prefix: str, identifier: str, max_age_minutes: int = 15) -> Optional[Any]:
        """
        Get cached data if available and fresh
        """
        cache_key = self._get_cache_key(prefix, identifier)
        cache_path = self._get_cache_path(cache_key)
        
        if not os.path.exists(cache_path):
            return None
        
        try:
            # Check file age
            file_time = datetime.fromtimestamp(os.path.getmtime(cache_path))
            age = datetime.now() - file_time
            
            if age > timedelta(minutes=max_age_minutes):
                # Cache expired
                os.remove(cache_path)
                return None
            
            # Load cached data
            with open(cache_path, 'rb') as f:
                cached_data = pickle.load(f)
            
            # Return data with metadata
            return {
                'data': cached_data,
                'cached_at': file_time,
                'age_minutes': age.total_seconds() / 60
            }
            
        except Exception as e:
            # If cache read fails, just return None
            return None
    
    def set(self, prefix: str, identifier: str, data: Any):
        """
        Store data in cache
        """
        cache_key = self._get_cache_key(prefix, identifier)
        cache_path = self._get_cache_path(cache_key)
        
        try:
            with open(cache_path, 'wb') as f:
                pickle.dump(data, f)
            return True
        except Exception as e:
            st.warning(f"Cache write failed: {e}")
            return False
    
    def clear(self, prefix: Optional[str] = None):
        """
        Clear cache (all or specific prefix)
        """
        try:
            if prefix:
                # Clear specific prefix
                for file in os.listdir(self.cache_dir):
                    if file.startswith(prefix):
                        os.remove(os.path.join(self.cache_dir, file))
            else:
                # Clear all
                for file in os.listdir(self.cache_dir):
                    os.remove(os.path.join(self.cache_dir, file))
            return True
        except Exception as e:
            return False
    
    def get_cache_stats(self) -> dict:
        """
        Get statistics about cache
        """
        try:
            files = os.listdir(self.cache_dir)
            total_size = sum(os.path.getsize(os.path.join(self.cache_dir, f)) for f in files)
            
            return {
                'total_items': len(files),
                'total_size_mb': total_size / (1024 * 1024),
                'cache_dir': self.cache_dir
            }
        except:
            return {'total_items': 0, 'total_size_mb': 0}


# Global cache manager instance
_cache_manager = None

def get_cache_manager() -> CacheManager:
    """Get or create global cache manager"""
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = CacheManager()
    return _cache_manager


# Streamlit caching decorators with optimized settings

@st.cache_data(ttl=900)  # 15 minutes
def cached_fetch_stock_data(ticker: str):
    """
    Cached wrapper for stock data fetching
    TTL: 15 minutes (reasonable for stock data)
    """
    from data_fetcher import fetch_stock_data
    return fetch_stock_data(ticker)


@st.cache_data(ttl=3600)  # 1 hour
def cached_get_company_info(ticker: str):
    """
    Cached wrapper for company info
    TTL: 1 hour (company info changes rarely)
    """
    from data_fetcher import IndianStockDataFetcher
    fetcher = IndianStockDataFetcher(ticker)
    return fetcher.get_company_info()


@st.cache_data(ttl=1800)  # 30 minutes
def cached_sector_analysis(ticker: str, metrics: dict):
    """
    Cached sector comparison
    TTL: 30 minutes
    """
    from sector_comparison import perform_sector_analysis
    return perform_sector_analysis(ticker, metrics)


@st.cache_data(ttl=86400)  # 24 hours
def cached_pdf_text_extraction(pdf_path: str):
    """
    Cache PDF text extraction (PDFs don't change)
    TTL: 24 hours
    """
    import fitz
    doc = fitz.open(pdf_path)
    text = ""
    for page in doc:
        text += page.get_text()
    doc.close()
    return text


def display_cache_info():
    """
    Display cache information in Streamlit sidebar
    """
    cache_mgr = get_cache_manager()
    stats = cache_mgr.get_cache_stats()
    
    with st.sidebar.expander("⚡ Cache Info"):
        st.write(f"**Cached Items**: {stats['total_items']}")
        st.write(f"**Cache Size**: {stats['total_size_mb']:.2f} MB")
        
        if st.button("Clear Cache"):
            cache_mgr.clear()
            st.cache_data.clear()
            st.success("Cache cleared!")
            st.rerun()


def preload_popular_stocks():
    """
    Background task to preload popular stocks into cache
    Call this on app startup
    """
    popular = ['RELIANCE', 'TCS', 'INFY', 'HDFCBANK', 'ICICIBANK']
    cache_mgr = get_cache_manager()
    
    for ticker in popular:
        # Check if already cached
        cached = cache_mgr.get('stock_data', ticker, max_age_minutes=15)
        if not cached:
            # Preload in background
            try:
                data = cached_fetch_stock_data(ticker)
                cache_mgr.set('stock_data', ticker, data)
            except:
                pass  # Silent fail for preloading
