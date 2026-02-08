"""
ENHANCED DASHBOARD ADDITIONS
Add these sections to the display_dashboard function after the price chart
"""

# Add after the price chart section (around line 330):

def add_enhanced_sections(data):
    """Add all enhanced sections to dashboard"""
    
    # Section 1: DATA QUALITY SCORE
    if data.get('validation_results'):
        st.divider()
        st.subheader("✅ Data Quality Assessment")
        
        quality = data['validation_results']['quality_score']
        validations = data['validation_results']['validations']
        
        col1, col2, col3 = st.columns([1, 2, 2])
        
        with col1:
            st.metric(
                "Quality Score",
                f"{quality['score']}/100",
                help="Based on data consistency and validation checks"
            )
            st.markdown(f"**Grade**: {quality['color']} {quality['grade']}")
        
        with col2:
            if validations.get('delta_validation'):
                severity = validations['delta_validation']['severity']
                insights = validations['delta_validation'].get('insights', [])
                
                st.markdown("**Delta Severity:**")
                st.write(severity)
                
                if insights:
                    for insight in insights[:2]:  # Show top 2
                        st.caption(insight)
        
        with col3:
            if quality.get('warnings'):
                st.warning("⚠️ Data Warnings:")
                for warning in quality['warnings']:
                    st.caption(f"• {warning}")
            else:
                st.success("🟢 All validations passed")
    
    # Section 2: HISTORICAL TRENDS
    if data.get('historical_trends'):
        st.divider()
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
            
            # Alerts
            if patterns.get('alerts'):
                st.warning("🚨 **Trend Alerts:**")
                for alert in patterns['alerts']:
                    st.write(f"• {alert}")
        
        # Prediction
        if trends.get('prediction'):
            with st.expander("🔮 Next Quarter Projection (Simple Model)"):
                pred = trends['prediction']
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.metric(
                        "Predicted Revenue Change",
                        f"{pred['revenue']['change']:+.1f}%",
                        help=f"Confidence: {pred['revenue']['confidence']}"
                    )
                
                with col2:
                    st.metric(
                        "Predicted Profit Change",
                        f"{pred['profit']['change']:+.1f}%",
                        help=f"Confidence: {pred['profit']['confidence']}"
                    )
                
                st.caption(f"⚠️ {pred['disclaimer']}")
    
    # Section 3: SECTOR COMPARISON
    if data.get('sector_analysis') and data['sector_analysis'].get('available'):
        st.divider()
        st.subheader(f"🏢 Sector Comparison: {data['sector_analysis']['sector']}")
        
        sector = data['sector_analysis']
        
        # Show comparison chart
        if sector.get('chart'):
            st.plotly_chart(sector['chart'], use_container_width=True)
        
        # Show key comparisons
        if sector.get('comparisons'):
            comps = sector['comparisons']
            
            cols = st.columns(len(comps))
            
            for idx, (metric, comp_data) in enumerate(comps.items()):
                with cols[idx]:
                    metric_name = metric.replace('_', ' ').title()
                    
                    st.metric(
                        metric_name,
                        f"{comp_data['value']:.1f}",
                        delta=f"Sector: {comp_data['sector_avg']:.1f}"
                    )
                    
                    verdict = comp_data.get('verdict', '')
                    if 'Below' in verdict or 'weak' in verdict.lower() or 'High Debt' in verdict:
                        st.caption(f"⚠️ {verdict}")
                    elif 'Above' in verdict or 'Strong' in verdict or 'Lower Debt' in verdict:
                        st.caption(f"✅ {verdict}")
                    else:
                        st.caption(f"➡️ {verdict}")
        
        # Show insights
        if sector.get('insights'):
            st.markdown("**💡 Sector Insights:**")
            for insight in sector['insights']:
                st.write(f"• {insight}")


# Instructions for integration:
"""
To integrate into app.py, add this after the price chart section (around line 330):

# After this line:
# st.plotly_chart(fig, use_container_width=True)

# Add:
add_enhanced_sections(data)

# Then continue with PDF insights section...
"""
