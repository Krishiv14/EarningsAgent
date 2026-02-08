"""
Multimodal Earnings Agent - Streamlit App
Main application file - WORKS WITH YOUR CURRENT FOLDER STRUCTURE
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from datetime import datetime
import sys
import os

# FIX: Since all files are in same directory as app.py, we don't need src prefix!
# Just import directly
try:
    from data_fetcher import IndianStockDataFetcher, fetch_stock_data
    from pdf_downloader import get_earnings_pdf
    from pdf_analyzer import analyze_earnings_report
    from data_validator import validate_stock_data
    from historical_trends import analyze_historical_trends
    from sector_comparison import perform_sector_analysis
    from caching import display_cache_info, cached_fetch_stock_data
except ImportError as e:
    st.error(f"Import error: {e}")
    st.info("Make sure all required files are in the same folder as app.py")
    st.stop()

# Page config
st.set_page_config(
    page_title="Earnings Agent - Indian Stock Market",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .alert-box {
        background-color: #fff3cd;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #ffc107;
        margin: 1rem 0;
    }
    .insight-box {
        background-color: #d1ecf1;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #17a2b8;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'analyzed_data' not in st.session_state:
    st.session_state.analyzed_data = None
if 'pdf_analyzer' not in st.session_state:
    st.session_state.pdf_analyzer = None


def main():
    # Header
    st.markdown('<div class="main-header">📊 Multimodal Earnings Agent</div>', unsafe_allow_html=True)
    st.markdown("##### AI-Powered Financial Analysis for Indian Stocks")
    
    # Sidebar
    with st.sidebar:
        st.header("🔍 Stock Selection")
        
        # Popular stocks for quick selection
        popular_stocks = {
            'RELIANCE': 'Reliance Industries',
            'TCS': 'Tata Consultancy Services',
            'INFY': 'Infosys',
            'HDFCBANK': 'HDFC Bank',
            'ICICIBANK': 'ICICI Bank',
            'ITC': 'ITC Limited',
            'SBIN': 'State Bank of India',
            'BHARTIARTL': 'Bharti Airtel',
            'HINDUNILVR': 'Hindustan Unilever'
        }
        
        selection_mode = st.radio(
            "Choose input method:",
            ["Popular Stocks", "Custom Ticker"]
        )
        
        if selection_mode == "Popular Stocks":
            selected = st.selectbox(
                "Select a stock:",
                options=list(popular_stocks.keys()),
                format_func=lambda x: f"{x} - {popular_stocks[x]}"
            )
            ticker = selected
        else:
            ticker = st.text_input(
                "Enter NSE Ticker:",
                placeholder="e.g., WIPRO, MARUTI, TITAN",
                help="Enter the ticker symbol without .NS suffix"
            )
        
        analyze_button = st.button("🚀 Analyze", type="primary", use_container_width=True)
        
        st.divider()
        
        # Mode indicator
        st.info("🆓 **FREE MODE**\nUsing Hugging Face AI")
        
        # Cache info
        try:
            display_cache_info()
        except Exception:
            pass  # Skip if caching has issues
        
        with st.expander("💰 Upgrade Info"):
            st.markdown("""
            **Current (Free):**
            - ✅ Full functionality
            - ⏱️ 5-10s analysis time
            - 🎯 70-80% accuracy
            
            **Paid Upgrade ($5 credits):**
            - ⚡ 1-2s analysis time
            - 🎯 90-95% accuracy
            - 🧠 Better insights
            
            [Get Claude API Key](https://console.anthropic.com/)
            """)
    
    # Main content
    if analyze_button and ticker:
        analyze_stock(ticker)
    
    # Display results if available
    if st.session_state.analyzed_data:
        display_dashboard(st.session_state.analyzed_data)


def analyze_stock(ticker: str):
    """Main analysis workflow with enhancements"""
    
    with st.spinner(f"🔍 Fetching data for {ticker}..."):
        # Step 1: Fetch financial data
        try:
            data_fetcher = IndianStockDataFetcher(ticker)
            
            company_info = data_fetcher.get_company_info()
            if not company_info:
                st.error("❌ Invalid ticker or data not available")
                return
            
            metrics = data_fetcher.get_financial_metrics()
            delta_info = data_fetcher.calculate_delta_analysis()
            price_history = data_fetcher.get_historical_price()
            quarterly_data = data_fetcher.get_quarterly_financials()
            
        except Exception as e:
            st.error(f"❌ Error fetching data: {e}")
            return
    
    # Step 2: Data Validation (NEW!)
    validation_results = None
    try:
        with st.spinner("✅ Validating data quality..."):
            validation_results = validate_stock_data(
                ticker, 
                metrics.get('current_price', 0) if metrics else 0,
                metrics or {},
                delta_info
            )
    except Exception as e:
        st.info(f"ℹ️ Validation skipped: {e}")
    
    # Step 3: Historical Trends (NEW!)
    historical_trends = None
    try:
        with st.spinner("📊 Analyzing historical trends..."):
            historical_trends = analyze_historical_trends(ticker, quarterly_data) if quarterly_data else None
    except Exception as e:
        st.info(f"ℹ️ Trend analysis skipped: {e}")
    
    # Step 4: Sector Comparison (NEW!)
    sector_analysis = None
    try:
        with st.spinner("🏢 Comparing with sector peers..."):
            sector_analysis = perform_sector_analysis(ticker, metrics) if metrics else None
    except Exception as e:
        st.info(f"ℹ️ Sector comparison skipped: {e}")
    
    # Step 5: Get PDF
    with st.spinner("📄 Looking for earnings report..."):
        pdf_path = get_earnings_pdf(ticker, allow_manual=True)
    
    # Step 6: Analyze PDF if available
    pdf_analysis = None
    if pdf_path and os.path.exists(pdf_path):
        with st.spinner("🤖 AI is analyzing the earnings report... (This may take 10-15 seconds)"):
            try:
                pdf_analysis = analyze_earnings_report(pdf_path, delta_info)
                if pdf_analysis:
                    st.session_state.pdf_analyzer = pdf_analysis['analyzer']
            except Exception as e:
                st.warning(f"⚠️ PDF analysis failed: {e}")
    
    # Store results with enhancements
    st.session_state.analyzed_data = {
        'ticker': ticker,
        'company_info': company_info,
        'metrics': metrics,
        'delta_info': delta_info,
        'price_history': price_history,
        'pdf_analysis': pdf_analysis,
        'validation_results': validation_results,
        'historical_trends': historical_trends,
        'sector_analysis': sector_analysis
    }
    
    st.success("✅ Analysis complete!")


def display_dashboard(data):
    """Display comprehensive dashboard"""
    
    ticker = data['ticker']
    company_info = data['company_info']
    metrics = data['metrics']
    delta_info = data['delta_info']
    price_history = data['price_history']
    pdf_analysis = data['pdf_analysis']
    
    # Company Header
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.header(f"{company_info['name']}")
        st.caption(f"**Sector:** {company_info['sector']} | **Industry:** {company_info['industry']}")
    
    with col2:
        st.metric(
            "Current Price",
            f"₹{metrics['current_price']:.2f}" if metrics else "N/A"
        )
    
    st.divider()
    
    # 🆕 DATA QUALITY SCORE (if available)
    if data.get('validation_results'):
        st.subheader("✅ Data Quality Assessment")
        
        quality = data['validation_results']['quality_score']
        validations = data['validation_results']['validations']
        
        col1, col2, col3 = st.columns([1, 2, 2])
        
        with col1:
            st.metric(
                "Quality Score",
                f"{quality['score']}/100",
                help="Based on data consistency checks"
            )
            st.markdown(f"**Grade**: {quality['color']} {quality['grade']}")
        
        with col2:
            if validations.get('delta_validation'):
                severity = validations['delta_validation']['severity']
                st.markdown("**Delta Severity:**")
                st.write(severity)
        
        with col3:
            if quality.get('warnings'):
                st.warning("⚠️ " + "; ".join(quality['warnings'][:2]))
            else:
                st.success("🟢 All checks passed")
        
        st.divider()
    
    # Key Metrics Row
    st.subheader("📊 Key Financial Metrics")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("P/E Ratio", f"{metrics['pe_ratio']:.2f}" if metrics and metrics['pe_ratio'] else "N/A")
    with col2:
        st.metric("P/B Ratio", f"{metrics['pb_ratio']:.2f}" if metrics and metrics['pb_ratio'] else "N/A")
    with col3:
        profit_margin = metrics['profit_margin'] * 100 if metrics and metrics['profit_margin'] else 0
        st.metric("Profit Margin", f"{profit_margin:.2f}%")
    with col4:
        roe = metrics['roe'] * 100 if metrics and metrics['roe'] else 0
        st.metric("ROE", f"{roe:.2f}%")
    
    st.divider()
    
    # 🎯 DELTA ANALYSIS - The Core Feature
    st.subheader("🎯 Delta Analysis - Revenue vs Profit")
    
    if delta_info and delta_info.get('delta_detected'):
        st.markdown(f'<div class="alert-box">⚠️ <strong>Anomaly Detected:</strong> {delta_info["delta_type"]}</div>', 
                   unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric(
                "Revenue Change",
                f"{delta_info['revenue_change_pct']:+.2f}%",
                delta=f"{delta_info['revenue_change_pct']:.2f}%"
            )
        
        with col2:
            st.metric(
                "Profit Change",
                f"{delta_info['profit_change_pct']:+.2f}%",
                delta=f"{delta_info['profit_change_pct']:.2f}%"
            )
        
        # AI Explanation
        if pdf_analysis and pdf_analysis.get('delta_analysis'):
            st.markdown('<div class="insight-box">', unsafe_allow_html=True)
            st.markdown("**🤖 AI Analyst Insight:**")
            st.write(pdf_analysis['delta_analysis'])
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.info("💡 Upload the earnings PDF to get AI-powered explanation of this anomaly")
    
    else:
        st.success("✅ No significant anomaly detected. Revenue and profit are moving in sync.")
        if delta_info:
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Revenue Change", f"{delta_info['revenue_change_pct']:+.2f}%")
            with col2:
                st.metric("Profit Change", f"{delta_info['profit_change_pct']:+.2f}%")
    
    st.divider()
    
    # 🆕 HISTORICAL TRENDS (if available)
    if data.get('historical_trends'):
        st.subheader("📈 Historical Trend Analysis (8 Quarters)")
        
        trends = data['historical_trends']
        
        if trends.get('chart'):
            st.plotly_chart(trends['chart'], use_container_width=True)
        
        if trends.get('patterns'):
            patterns = trends['patterns']
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown("**Revenue Trend:**")
                st.write(patterns.get('revenue_trend', 'N/A'))
            
            with col2:
                st.markdown("**Profit Trend:**")
                st.write(patterns.get('profit_trend', 'N/A'))
            
            with col3:
                st.markdown("**Margin Trend:**")
                st.write(patterns.get('margin_trend', 'N/A'))
            
            if patterns.get('alerts'):
                st.warning("🚨 **Alerts:** " + " | ".join(patterns['alerts']))
        
        st.divider()
    
    # 🆕 SECTOR COMPARISON (if available)
    if data.get('sector_analysis') and data['sector_analysis'].get('available'):
        st.subheader(f"🏢 Sector Comparison: {data['sector_analysis']['sector']}")
        
        sector = data['sector_analysis']
        
        if sector.get('chart'):
            st.plotly_chart(sector['chart'], use_container_width=True)
        
        if sector.get('insights'):
            st.markdown("**💡 Sector Insights:**")
            for insight in sector['insights']:
                st.write(f"• {insight}")
        
        st.divider()
    
    # Price Chart
    st.subheader("📈 Stock Price Trend (1 Year)")
    
    if price_history is not None and not price_history.empty:
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=price_history.index,
            y=price_history['Close'],
            mode='lines',
            name='Close Price',
            line=dict(color='#1f77b4', width=2)
        ))
        
        fig.update_layout(
            xaxis_title="Date",
            yaxis_title="Price (₹)",
            hovermode='x unified',
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # PDF Insights Section
    if pdf_analysis:
        st.divider()
        st.subheader("📄 Earnings Report Insights")
        
        tab1, tab2, tab3 = st.tabs(["💬 Ask Questions", "📝 Key Excerpts", "📊 Extracted Data"])
        
        with tab1:
            st.markdown("**Ask questions about the earnings report:**")
            
            question = st.text_input(
                "Your question:",
                placeholder="e.g., What were the main challenges faced this quarter?",
                key="pdf_question"
            )
            
            if st.button("🔍 Get Answer") and question:
                if st.session_state.pdf_analyzer:
                    with st.spinner("🤖 Analyzing..."):
                        answer = st.session_state.pdf_analyzer.answer_question(question)
                        st.markdown(f'<div class="insight-box"><strong>Answer:</strong><br>{answer}</div>', 
                                   unsafe_allow_html=True)
        
        with tab2:
            if pdf_analysis.get('notes'):
                st.markdown("**Notes to Accounts:**")
                st.text_area("", pdf_analysis['notes'][:1000] + "...", height=200, key="notes_display")
            
            if pdf_analysis.get('commentary'):
                st.markdown("**Management Commentary:**")
                st.text_area("", pdf_analysis['commentary'][:1000] + "...", height=200, key="commentary_display")
        
        with tab3:
            extracted = pdf_analysis.get('extracted_metrics', {})
            if any(extracted.values()):
                st.markdown("**Auto-extracted metrics from PDF:**")
                
                df = pd.DataFrame([
                    {"Metric": "Revenue", "Value": extracted.get('revenue', 'N/A')},
                    {"Metric": "Profit", "Value": extracted.get('profit', 'N/A')},
                    {"Metric": "EPS", "Value": extracted.get('eps', 'N/A')}
                ])
                
                st.dataframe(df, use_container_width=True)


# Run app
if __name__ == "__main__":
    main()
