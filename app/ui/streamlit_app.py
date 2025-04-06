import streamlit as st
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from typing import List, Dict, Any
import validators
import time
from app.scraper.cohesive_clone import CohesiveScraper
from app.ui.components import (
    render_header,
    render_filters,
    render_url_input,
    render_progress,
    render_results,
    render_error,
    render_success
)
from app.config import SCRAPING_CONFIG

def validate_urls(urls: str) -> List[str]:
    """Validate and clean URLs"""
    if not urls:
        return []
        
    url_list = [url.strip() for url in urls.split('\n') if url.strip()]
    valid_urls = [url for url in url_list if validators.url(url)]
    
    if not valid_urls:
        render_error("Please enter valid URLs")
        return []
        
    if len(valid_urls) > SCRAPING_CONFIG['max_urls_per_batch']:
        render_error(f"Maximum {SCRAPING_CONFIG['max_urls_per_batch']} URLs allowed per batch")
        return []
        
    return valid_urls

def validate_scraped_data(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Validate and clean scraped data"""
    if not data:
        return []
    
    valid_data = []
    required_fields = ['name', 'website']
    
    for item in data:
        if not isinstance(item, dict):
            continue
            
        # Ensure all required fields exist
        if not all(field in item for field in required_fields):
            continue
            
        # Ensure no None values in required fields
        if any(item[field] is None for field in required_fields):
            continue
            
        valid_data.append(item)
        
    return valid_data

def apply_filters(data: List[Dict[str, Any]], filters: Dict) -> List[Dict[str, Any]]:
    """Apply filters to scraped data"""
    if not data:
        return []
        
    filtered_data = data.copy()
    
    # Apply basic filters
    if filters['min_employees'] > 0:
        filtered_data = [
            d for d in filtered_data
            if d.get('employees', 0) >= filters['min_employees']
        ]
        
    if filters['industry']:
        filtered_data = [
            d for d in filtered_data
            if d.get('industry') in filters['industry']
        ]
        
    if filters['location']:
        locations = [loc.strip().lower() for loc in filters['location'].split(',')]
        filtered_data = [
            d for d in filtered_data
            if any(loc in str(d.get('location', '')).lower() for loc in locations)
        ]
        
    if filters['technologies']:
        filtered_data = [
            d for d in filtered_data
            if any(tech in d.get('technologies', []) for tech in filters['technologies'])
        ]
    
    # Apply advanced filters
    if filters['has_email']:
        filtered_data = [d for d in filtered_data if d.get('email')]
        
    if filters['has_social']:
        filtered_data = [
            d for d in filtered_data
            if d.get('social_links') and len(d['social_links']) > 0
        ]
        
    if filters['min_revenue'] != "0":
        revenue_map = {
            "1M": 1000000,
            "5M": 5000000,
            "10M": 10000000,
            "50M": 50000000,
            "100M": 100000000,
            "500M": 500000000,
            "1B+": 1000000000
        }
        min_revenue = revenue_map[filters['min_revenue']]
        filtered_data = [
            d for d in filtered_data
            if d.get('revenue', 0) >= min_revenue
        ]
        
    return filtered_data

def main():
    """Main application entry point"""
    try:
        render_header()
        
        # Initialize session state
        if 'scraping_results' not in st.session_state:
            st.session_state.scraping_results = []
            
        # Initialize scraper
        scraper = CohesiveScraper()
        
        # Render filters
        filters = render_filters()
        
        # Main content
        col1, col2 = st.columns([2, 1])
        
        with col1:
            urls = render_url_input()
            
            if st.button("Start Scraping", type="primary"):
                valid_urls = validate_urls(urls)
                
                if valid_urls:
                    # Initialize progress tracking
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    # Scrape data
                    results = []
                    for idx, url in enumerate(valid_urls):
                        status_text.text(f"Scraping {url}...")
                        
                        try:
                            result = scraper.scrape_company_info(url)
                            if result:
                                results.append(result)
                        except Exception as e:
                            render_error(f"Error scraping {url}: {str(e)}")
                            continue
                            
                        # Update progress
                        progress = (idx + 1) / len(valid_urls)
                        progress_bar.progress(progress)
                        
                        # Add delay to prevent rate limiting
                        time.sleep(SCRAPING_CONFIG['delay_between_requests'])
                    
                    # Validate and clean results
                    valid_results = validate_scraped_data(results)
                    
                    if not valid_results:
                        render_error("No valid data was scraped")
                        return
                    
                    # Store results in session state
                    st.session_state.scraping_results = valid_results
                    
                    # Apply filters and display results
                    filtered_results = apply_filters(valid_results, filters)
                    
                    if filtered_results:
                        render_success(f"Successfully scraped {len(filtered_results)} companies")
                        try:
                            render_results(filtered_results)
                        except Exception as e:
                            render_error(f"Error displaying results: {str(e)}")
                    else:
                        render_error("No data matched the selected filters")
        
        with col2:
            st.subheader("Instructions")
            st.markdown("""
            ### How to Use
            1. Enter company URLs in the text area
            2. Configure filters in the sidebar
            3. Click 'Start Scraping'
            4. Review and export results
            
            ### Features
            - Multi-URL processing
            - Advanced filtering
            - Data validation
            - Export capabilities
            - Data visualization
            
            ### Best Practices
            - Start with a small batch of URLs
            - Use filters to focus on relevant leads
            - Export data regularly
            - Respect website terms of service
            
            ### Note
            Please ensure you have permission to scrape target websites
            and comply with their terms of service.
            """)
            
    except Exception as e:
        render_error(f"An unexpected error occurred: {str(e)}")

if __name__ == "__main__":
    main()