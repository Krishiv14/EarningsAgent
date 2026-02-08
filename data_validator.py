"""
Data Validation Module
Cross-validates financial data from multiple sources
"""

import yfinance as yf
import requests
import pandas as pd
from datetime import datetime
import streamlit as st
from typing import Dict, Optional


class DataValidator:
    """
    Validates financial data quality and consistency
    Cross-checks yfinance against other sources when possible
    """
    
    def __init__(self, ticker: str):
        self.ticker = ticker
        self.validation_results = {}
        
    def validate_price_data(self, yf_price: float) -> Dict:
        """
        Validate current price against multiple sources
        Returns: validation score and warnings
        """
        validation = {
            'price': yf_price,
            'sources_checked': 1,
            'discrepancies': [],
            'confidence': 'High',
            'warnings': []
        }
        
        # In production, you'd check NSE/BSE APIs here
        # For now, we do basic sanity checks
        
        # Check 1: Price is reasonable (not zero, not negative)
        if yf_price <= 0:
            validation['warnings'].append("⚠️ Invalid price data (≤0)")
            validation['confidence'] = 'Low'
        
        # Check 2: Price hasn't changed more than 20% in a day (circuit limit check)
        # This would require historical data comparison
        
        return validation
    
    def validate_financial_metrics(self, metrics: Dict) -> Dict:
        """
        Validate financial ratios make sense
        """
        validation = {
            'valid': True,
            'warnings': [],
            'flags': []
        }
        
        # Check P/E ratio
        if metrics.get('pe_ratio'):
            pe = metrics['pe_ratio']
            if pe < 0:
                validation['warnings'].append("⚠️ Negative P/E ratio (company has losses)")
            elif pe > 100:
                validation['flags'].append("📊 Very high P/E ratio (>100) - overvalued or growth stock")
        
        # Check Debt to Equity
        if metrics.get('debt_to_equity'):
            de = metrics['debt_to_equity']
            if de > 2:
                validation['warnings'].append("⚠️ High debt levels (D/E > 2)")
        
        # Check ROE
        if metrics.get('roe'):
            roe = metrics['roe'] * 100 if metrics['roe'] < 1 else metrics['roe']
            if roe < 0:
                validation['warnings'].append("⚠️ Negative ROE (company is unprofitable)")
            elif roe > 30:
                validation['flags'].append("🌟 Exceptional ROE (>30%) - strong performer")
        
        # Check Profit Margin
        if metrics.get('profit_margin'):
            pm = metrics['profit_margin'] * 100 if metrics['profit_margin'] < 1 else metrics['profit_margin']
            if pm < 0:
                validation['warnings'].append("⚠️ Negative profit margin")
            elif pm > 25:
                validation['flags'].append("🌟 High profit margin (>25%)")
        
        return validation
    
    def validate_delta_analysis(self, delta_info: Dict) -> Dict:
        """
        Validate if delta analysis makes sense
        Flag unusual patterns
        """
        if not delta_info:
            return {'valid': False, 'reason': 'No delta data'}
        
        validation = {
            'valid': True,
            'severity': 'Normal',
            'insights': []
        }
        
        rev_change = delta_info.get('revenue_change_pct', 0)
        profit_change = delta_info.get('profit_change_pct', 0)
        
        # Calculate divergence magnitude
        divergence = abs(rev_change - profit_change)
        
        # Severity levels
        if divergence > 30:
            validation['severity'] = 'Critical'
            validation['insights'].append("🔴 CRITICAL: >30% divergence - major issue")
        elif divergence > 20:
            validation['severity'] = 'High'
            validation['insights'].append("🟠 HIGH: >20% divergence - investigate immediately")
        elif divergence > 10:
            validation['severity'] = 'Medium'
            validation['insights'].append("🟡 MEDIUM: >10% divergence - needs attention")
        else:
            validation['severity'] = 'Low'
            validation['insights'].append("🟢 LOW: <10% divergence - normal variation")
        
        # Pattern detection
        if rev_change > 0 and profit_change < 0:
            validation['insights'].append("📉 Revenue growing but profit declining - INVESTIGATE COSTS")
        elif rev_change < 0 and profit_change > 0:
            validation['insights'].append("📈 Revenue falling but profit rising - COST CUTTING SUCCESS?")
        elif rev_change > 15 and profit_change > 15:
            validation['insights'].append("🚀 Strong growth in both revenue and profit - HEALTHY")
        elif rev_change < -15 and profit_change < -15:
            validation['insights'].append("⚠️ Both revenue and profit declining - STRUGGLING")
        
        return validation
    
    def check_data_freshness(self, last_updated: datetime) -> Dict:
        """
        Check how old the data is
        """
        if not last_updated:
            return {'fresh': False, 'age': 'Unknown', 'warning': 'No timestamp'}
        
        now = datetime.now()
        age_days = (now - last_updated).days
        
        freshness = {
            'fresh': age_days < 7,
            'age_days': age_days,
            'warning': None
        }
        
        if age_days > 30:
            freshness['warning'] = f"⚠️ Data is {age_days} days old - may be outdated"
        elif age_days > 7:
            freshness['warning'] = f"📅 Data is {age_days} days old"
        
        return freshness
    
    def generate_quality_score(self, validations: Dict) -> Dict:
        """
        Generate overall data quality score
        """
        score = 100
        warnings = []
        
        # Deduct points for issues
        if validations.get('price_validation', {}).get('confidence') == 'Low':
            score -= 30
            warnings.append("Low confidence in price data")
        
        metric_warnings = validations.get('metrics_validation', {}).get('warnings', [])
        score -= len(metric_warnings) * 10
        
        # Cap at 0
        score = max(0, score)
        
        # Grade
        if score >= 90:
            grade = 'A (Excellent)'
            color = '🟢'
        elif score >= 75:
            grade = 'B (Good)'
            color = '🟡'
        elif score >= 60:
            grade = 'C (Fair)'
            color = '🟠'
        else:
            grade = 'D (Poor)'
            color = '🔴'
        
        return {
            'score': score,
            'grade': grade,
            'color': color,
            'warnings': warnings
        }


def validate_stock_data(ticker: str, price: float, metrics: Dict, delta_info: Dict) -> Dict:
    """
    Main validation function - validates all data for a stock
    """
    validator = DataValidator(ticker)
    
    validations = {
        'price_validation': validator.validate_price_data(price),
        'metrics_validation': validator.validate_financial_metrics(metrics),
        'delta_validation': validator.validate_delta_analysis(delta_info)
    }
    
    # Generate quality score
    quality = validator.generate_quality_score(validations)
    
    return {
        'validations': validations,
        'quality_score': quality
    }
