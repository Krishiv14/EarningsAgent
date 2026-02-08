"""
PDF Analyzer Module
Extracts text from PDFs and uses FREE Hugging Face models for analysis
"""

import fitz  # PyMuPDF
import requests
import json
import streamlit as st
from typing import Dict, List, Optional
import os
import re
from collections import defaultdict


class PDFAnalyzer:
    """
    Analyze earnings PDFs using free AI models
    Uses Hugging Face Inference API (completely free)
    """
    
    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path
        self.text_content = ""
        self.pages_text = []
        
    def extract_text(self):
        """Extract text from PDF using PyMuPDF with enhanced table detection"""
        try:
            doc = fitz.open(self.pdf_path)
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                
                # Extract text
                text = page.get_text()
                
                # Try to detect tables
                tables = self._detect_tables_from_page(page)
                
                self.pages_text.append({
                    'page': page_num + 1,
                    'text': text,
                    'tables': tables,
                    'has_tables': len(tables) > 0
                })
                self.text_content += text + "\n\n"
            
            doc.close()
            return True
            
        except Exception as e:
            st.error(f"PDF extraction error: {e}")
            return False
    
    def _detect_tables_from_page(self, page) -> List[Dict]:
        """
        Detect table-like structures in PDF page
        Returns list of detected tables with their data
        """
        tables = []
        
        try:
            # Get all text blocks with positions
            blocks = page.get_text("dict")["blocks"]
            
            # Look for aligned text (potential table columns)
            rows = defaultdict(list)
            
            for block in blocks:
                if "lines" in block:
                    for line in block["lines"]:
                        y_pos = round(line["bbox"][1])  # Y position
                        for span in line["spans"]:
                            text = span["text"].strip()
                            if text:
                                rows[y_pos].append({
                                    'text': text,
                                    'x': span["bbox"][0],
                                    'y': y_pos
                                })
            
            # Identify table rows (rows with multiple aligned elements)
            table_rows = []
            for y_pos, elements in rows.items():
                if len(elements) >= 2:  # At least 2 columns
                    # Sort by x position
                    elements.sort(key=lambda e: e['x'])
                    table_rows.append(elements)
            
            # Group consecutive rows into tables
            if table_rows:
                current_table = []
                for row in table_rows:
                    if not current_table or abs(row[0]['y'] - current_table[-1][0]['y']) < 20:
                        current_table.append(row)
                    else:
                        if len(current_table) >= 3:
                            tables.append({
                                'rows': len(current_table),
                                'columns': max(len(r) for r in current_table),
                                'data': current_table
                            })
                        current_table = [row]
                
                # Add last table
                if len(current_table) >= 3:
                    tables.append({
                        'rows': len(current_table),
                        'columns': max(len(r) for r in current_table),
                        'data': current_table
                    })
        
        except Exception:
            pass  # Silent fail for table detection
        
        return tables
    
    def find_notes_to_accounts(self) -> str:
        """
        Find 'Notes to Accounts' section in the PDF
        """
        notes_text = ""
        
        for page_data in self.pages_text:
            text = page_data['text'].lower()
            
            # Look for common section headers
            if any(keyword in text for keyword in [
                'notes to accounts',
                'notes to financial statements',
                'explanatory notes',
                'significant accounting policies'
            ]):
                notes_text += page_data['text'] + "\n\n"
        
        return notes_text if notes_text else self.text_content[:3000]
    
    def find_management_commentary(self) -> str:
        """Find management discussion section"""
        commentary = ""
        
        for page_data in self.pages_text:
            text = page_data['text'].lower()
            
            if any(keyword in text for keyword in [
                'management discussion',
                "directors' report",
                'management commentary',
                'operational highlights'
            ]):
                commentary += page_data['text'] + "\n\n"
        
        return commentary if commentary else ""
    
    def call_huggingface_model(self, prompt: str, max_length=512) -> str:
        """
        Call Hugging Face Inference API (FREE)
        """
        models = [
            "microsoft/Phi-3-mini-4k-instruct",
            "meta-llama/Llama-3.2-3B-Instruct",
            "mistralai/Mistral-7B-Instruct-v0.2"
        ]
        
        for model in models:
            try:
                api_url = f"https://api-inference.huggingface.co/models/{model}"
                
                headers = {}
                hf_token = os.getenv('HF_TOKEN')
                if hf_token:
                    headers["Authorization"] = f"Bearer {hf_token}"
                
                payload = {
                    "inputs": prompt,
                    "parameters": {
                        "max_new_tokens": max_length,
                        "temperature": 0.7,
                        "top_p": 0.9
                    }
                }
                
                response = requests.post(api_url, headers=headers, json=payload, timeout=30)
                
                if response.status_code == 200:
                    result = response.json()
                    
                    if isinstance(result, list) and len(result) > 0:
                        return result[0].get('generated_text', '').replace(prompt, '').strip()
                    elif isinstance(result, dict):
                        return result.get('generated_text', '').replace(prompt, '').strip()
                
                elif response.status_code == 503:
                    st.info(f"Model {model} is loading... trying next model")
                    continue
                    
            except Exception as e:
                st.warning(f"Model {model} failed: {e}")
                continue
        
        return "AI analysis temporarily unavailable. Please try again in a moment."
    
    def analyze_delta(self, delta_info: Dict) -> str:
        """
        Analyze WHY there's a delta between revenue and profit
        """
        if not delta_info or not delta_info.get('delta_detected'):
            return "No significant delta detected between revenue and profit trends."
        
        notes = self.find_notes_to_accounts()
        
        prompt = f"""You are a financial analyst. Analyze this company's quarterly results.

SITUATION:
- Revenue changed by {delta_info['revenue_change_pct']}%
- Profit changed by {delta_info['profit_change_pct']}%
- Pattern: {delta_info['delta_type']}

NOTES FROM EARNINGS REPORT:
{notes[:1500]}

TASK: Explain in 2-3 sentences WHY profit didn't follow revenue. Look for:
- Cost increases (raw materials, labor)
- One-time expenses or write-offs
- Tax changes or provisions
- Operational inefficiencies

Keep it concise and specific."""

        analysis = self.call_huggingface_model(prompt, max_length=300)
        return analysis
    
    def extract_key_metrics(self) -> Dict:
        """
        Extract key numbers from PDF using pattern matching and table detection
        """
        metrics = {
            'revenue': None,
            'profit': None,
            'ebitda': None,
            'eps': None,
            'total_income': None,
            'total_expenses': None
        }
        
        # Method 1: Try to find in detected tables
        for page_data in self.pages_text:
            if page_data.get('has_tables'):
                for table in page_data['tables']:
                    metrics_from_table = self._extract_from_table(table)
                    for key, value in metrics_from_table.items():
                        if value is not None:
                            metrics[key] = value
        
        # Method 2: Regex patterns
        patterns = {
            'revenue': r'(?:Total Revenue|Net Sales|Total Income|Revenue from Operations)[:\s]+(?:Rs\.?|INR|₹)?\s*([0-9,]+\.?[0-9]*)',
            'profit': r'(?:Net Profit|PAT|Profit After Tax|Profit for the period)[:\s]+(?:Rs\.?|INR|₹)?\s*([0-9,]+\.?[0-9]*)',
            'eps': r'(?:EPS|Earnings Per Share|Basic EPS)[:\s]+(?:Rs\.?|INR|₹)?\s*([0-9,]+\.?[0-9]*)',
            'ebitda': r'(?:EBITDA)[:\s]+(?:Rs\.?|INR|₹)?\s*([0-9,]+\.?[0-9]*)'
        }
        
        for key, pattern in patterns.items():
            if metrics[key] is None:
                match = re.search(pattern, self.text_content, re.IGNORECASE)
                if match:
                    try:
                        value = match.group(1).replace(',', '')
                        metrics[key] = float(value)
                    except:
                        pass
        
        return metrics
    
    def _extract_from_table(self, table: Dict) -> Dict:
        """Extract financial metrics from detected table structure"""
        metrics = {}
        
        try:
            rows = table['data']
            
            for row in rows:
                row_text = ' '.join([cell['text'] for cell in row])
                
                if any(keyword in row_text.lower() for keyword in ['revenue', 'income', 'profit', 'eps']):
                    numbers = re.findall(r'([0-9,]+\.?[0-9]*)', row_text)
                    
                    if numbers:
                        try:
                            value = float(numbers[0].replace(',', ''))
                            
                            if 'revenue' in row_text.lower() or 'sales' in row_text.lower():
                                metrics['revenue'] = value
                            elif 'profit' in row_text.lower() or 'pat' in row_text.lower():
                                metrics['profit'] = value
                            elif 'eps' in row_text.lower():
                                metrics['eps'] = value
                            elif 'ebitda' in row_text.lower():
                                metrics['ebitda'] = value
                        except:
                            pass
        except:
            pass
        
        return metrics
    
    def answer_question(self, question: str) -> str:
        """
        RAG-style Q&A: Answer questions about the earnings report
        """
        context = self.text_content[:2000]
        
        prompt = f"""Based on this earnings report excerpt, answer the question concisely.

REPORT EXCERPT:
{context}

QUESTION: {question}

ANSWER (2-3 sentences max):"""

        answer = self.call_huggingface_model(prompt, max_length=200)
        return answer


def analyze_earnings_report(pdf_path: str, delta_info: Optional[Dict] = None):
    """
    Main function to analyze earnings report
    """
    analyzer = PDFAnalyzer(pdf_path)
    
    if not analyzer.extract_text():
        return None
    
    delta_analysis = None
    if delta_info:
        delta_analysis = analyzer.analyze_delta(delta_info)
    
    metrics = analyzer.extract_key_metrics()
    
    return {
        'text_content': analyzer.text_content,
        'notes': analyzer.find_notes_to_accounts(),
        'commentary': analyzer.find_management_commentary(),
        'delta_analysis': delta_analysis,
        'extracted_metrics': metrics,
        'analyzer': analyzer
    }
