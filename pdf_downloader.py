"""
PDF Downloader Module
Downloads quarterly earnings PDFs from BSE/NSE websites
"""

import requests
from bs4 import BeautifulSoup
import os
from datetime import datetime
import streamlit as st


class EarningsReportDownloader:
    """Download earnings reports from Indian stock exchanges"""
    
    def __init__(self, ticker: str):
        self.ticker = ticker.replace('.NS', '').replace('.BO', '')
        self.download_dir = "data/pdfs"
        os.makedirs(self.download_dir, exist_ok=True)
    
    def get_bse_code(self, ticker):
        """
        Map NSE ticker to BSE code (scrip code)
        This is a simplified mapping - in production, use a database
        """
        # Common ticker to BSE code mappings
        ticker_map = {
            'RELIANCE': '500325',
            'TCS': '532540',
            'INFY': '500209',
            'HDFCBANK': '500180',
            'ICICIBANK': '532174',
            'HINDUNILVR': '500696',
            'ITC': '500875',
            'SBIN': '500112',
            'BHARTIARTL': '532454',
            'KOTAKBANK': '500247',
            'LT': '500510',
            'ASIANPAINT': '500820',
            'AXISBANK': '532215',
            'MARUTI': '532500',
            'TITAN': '500114',
            'WIPRO': '507685',
            'ULTRACEMCO': '532538',
            'BAJFINANCE': '500034',
            'HCLTECH': '532281',
            'TECHM': '532755'
        }
        
        return ticker_map.get(ticker.upper(), None)
    
    def download_from_bse(self, scrip_code):
        """
        Download latest quarterly results from BSE
        """
        try:
            # BSE Corporate Announcements API
            url = f"https://api.bseindia.com/BseIndiaAPI/api/AnnGetData/w"
            
            params = {
                'scripcode': scrip_code,
                'news': 'Quarterly Results',
                'page': '1'
            }
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(url, params=params, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                # Extract PDF URL from response
                if 'Table' in data and len(data['Table']) > 0:
                    latest = data['Table'][0]
                    pdf_url = latest.get('ATTACHMENTNAME', '')
                    
                    if pdf_url:
                        return self._download_pdf(pdf_url, f"{self.ticker}_BSE_quarterly.pdf")
            
            return None
            
        except Exception as e:
            st.warning(f"BSE download failed: {e}")
            return None
    
    def _download_pdf(self, url, filename):
        """Download PDF from URL"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=30)
            
            if response.status_code == 200:
                filepath = os.path.join(self.download_dir, filename)
                
                with open(filepath, 'wb') as f:
                    f.write(response.content)
                
                return filepath
            
            return None
            
        except Exception as e:
            st.error(f"PDF download error: {e}")
            return None
    
    def get_latest_report(self):
        """
        Main method to get latest earnings report
        Tries BSE first, then manual upload
        """
        # Try BSE
        bse_code = self.get_bse_code(self.ticker)
        
        if bse_code:
            pdf_path = self.download_from_bse(bse_code)
            if pdf_path:
                return pdf_path
        
        # If all fails, return None
        st.info(f"Could not auto-download PDF for {self.ticker}. You can upload manually below.")
        return None
    
    def manual_upload_handler(self):
        """
        Streamlit file uploader for manual PDF upload
        """
        uploaded_file = st.file_uploader(
            "Upload Quarterly Results PDF (if auto-download failed)",
            type=['pdf'],
            help="Download from company's investor relations page"
        )
        
        if uploaded_file:
            filepath = os.path.join(self.download_dir, f"{self.ticker}_manual.pdf")
            
            with open(filepath, 'wb') as f:
                f.write(uploaded_file.getbuffer())
            
            return filepath
        
        return None


# Utility function
def get_earnings_pdf(ticker: str, allow_manual=True):
    """
    Get earnings PDF - auto-download or manual upload
    """
    downloader = EarningsReportDownloader(ticker)
    
    # Try auto-download
    pdf_path = downloader.get_latest_report()
    
    # If failed and manual upload allowed
    if not pdf_path and allow_manual:
        pdf_path = downloader.manual_upload_handler()
    
    return pdf_path
