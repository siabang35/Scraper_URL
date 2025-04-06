import streamlit as st
from typing import List, Dict, Any, Optional
import pandas as pd
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
from ..scraper.utils import save_to_file
import validators

def render_header():
    """Render application header with styling"""
    st.set_page_config(
        page_title="Lead Generation Tool",
        page_icon="🎯",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    st.markdown("""
        <style>
        .main-header {
            font-size: 2.5rem;
            font-weight: 700;
            color: #1E3A8A;
            margin-bottom: 1rem;
        }
        .sub-header {
            font-size: 1.2rem;
            color: #6B7280;
            margin-bottom: 2rem;
        }
        .stat-card {
            padding: 1rem;
            background-color: #F3F4F6;
            border-radius: 0.5rem;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }
        .stat-value {
            font-size: 1.8rem;
            font-weight: 600;
            color: #1E3A8A;
        }
        .stat-label {
            font-size: 0.9rem;
            color: #6B7280;
        }
        </style>
    """, unsafe_allow_html=True)
    
    st.markdown('<h1 class="main-header">🎯 Advanced Lead Generation Scraper</h1>', unsafe_allow_html=True)
    st.markdown(
        '<p class="sub-header">Extract valuable business leads with our intelligent scraping tool.</p>',
        unsafe_allow_html=True
    )

def render_filters():
    """Render advanced filtering options"""
    st.sidebar.title("Filters")
    
    with st.sidebar.expander("Company Filters", expanded=True):
        filters = {
            'min_employees': st.number_input(
                "Minimum Employees",
                min_value=0,
                help="Filter companies by minimum number of employees"
            ),
            'industry': st.multiselect(
                "Industry",
                ["Technology", "Healthcare", "Finance", "Retail", "Manufacturing", "Education", "Real Estate"],
                help="Select one or more industries"
            ),
            'location': st.text_input(
                "Location Keywords",
                help="Enter location keywords (comma-separated)"
            ),
            'founded_after': st.number_input(
                "Founded After Year",
                min_value=1800,
                max_value=datetime.now().year,
                value=2000,
                help="Filter companies founded after this year"
            ),
            'technologies': st.multiselect(
                "Technologies",
                ["Python", "JavaScript", "React", "AWS", "Azure", "Docker", "Kubernetes", "TensorFlow"],
                help="Select technologies used by the company"
            )
        }
    
    with st.sidebar.expander("Advanced Filters", expanded=False):
        advanced_filters = {
            'min_revenue': st.select_slider(
                "Minimum Revenue",
                options=["0", "1M", "5M", "10M", "50M", "100M", "500M", "1B+"],
                value="0",
                help="Filter by minimum company revenue"
            ),
            'has_email': st.checkbox(
                "Has Email Contact",
                help="Only show companies with valid email contacts"
            ),
            'has_social': st.checkbox(
                "Has Social Media",
                help="Only show companies with social media presence"
            )
        }
        
    filters.update(advanced_filters)
    return filters

def render_url_input() -> str:
    """Render enhanced URL input section"""
    st.subheader("Add Target URLs")
    
    col1, col2 = st.columns([3, 1])
    
    urls = ""
    url_list = []

    with col1:
        urls = st.text_area(
            "Enter URLs (one per line)",
            help="Enter company website URLs to scrape, one per line",
            height=100
        )
        
    with col2:
        st.markdown("### Quick Actions")
        if st.button("Validate URLs"):
            if urls.strip():
                url_list = [url.strip() for url in urls.split('\n') if url.strip()]
                valid_count = sum(1 for url in url_list if validators.url(url))
                invalid_urls = [url for url in url_list if not validators.url(url)]

                st.success(f"✅ Valid URLs: {valid_count}/{len(url_list)}")

                if invalid_urls:
                    st.warning("⚠️ Invalid URLs found:")
                    for bad_url in invalid_urls:
                        st.markdown(f"- `{bad_url}`")
            else:
                st.warning("Please enter at least one URL.")
    
    return urls

def render_progress(current: int, total: int, status: str):
    """Render progress bar with status"""
    progress = current / total
    
    st.progress(progress)
    st.markdown(f"**Status:** {status}")
    
    if current > 0:
        eta = (total - current) * 2  # Estimate 2 seconds per URL
        st.markdown(f"**Estimated time remaining:** {eta} seconds")

def render_results(data: List[Dict[str, Any]]):
    """Render comprehensive results dashboard"""
    if not data:
        st.warning("No data available to display.")
        return
        
    df = pd.DataFrame(data)
    
    # Summary metrics
    st.subheader("Summary Metrics")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Total Companies",
            len(df),
            help="Total number of companies scraped"
        )
    with col2:
        email_count = df['email'].notna().sum() if 'email' in df.columns else 0
        st.metric(
            "Valid Emails Found",
            email_count,
            help="Number of companies with valid email contacts"
        )
    with col3:
        industry_count = df['industry'].nunique() if 'industry' in df.columns else 0
        st.metric(
            "Industries Found",
            industry_count,
            help="Number of unique industries"
        )
    with col4:
        avg_employees = df['employees'].mean() if 'employees' in df.columns else 0
        st.metric(
            "Avg. Company Size",
            f"{avg_employees:.0f}",
            help="Average number of employees"
        )
    
    # Data visualizations
    st.subheader("Data Analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Industry distribution
        if 'industry' in df.columns and not df['industry'].isna().all():
            industry_counts = df['industry'].value_counts()
            fig = px.pie(
                values=industry_counts.values,
                names=industry_counts.index,
                title="Industry Distribution"
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No industry data available for visualization")
            
    with col2:
        # Company size distribution
        if 'employees' in df.columns and not df['employees'].isna().all():
            fig = px.histogram(
                df,
                x='employees',
                title="Company Size Distribution",
                nbins=20
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No employee data available for visualization")
    
    # Detailed results table
    st.subheader("Detailed Results")
    
    # Add column configuration for available columns
    column_config = {}
    if 'name' in df.columns:
        column_config['name'] = st.column_config.TextColumn("Company Name")
    if 'website' in df.columns:
        column_config['website'] = st.column_config.LinkColumn("Website")
    if 'email' in df.columns:
        column_config['email'] = st.column_config.TextColumn("Email")
    if 'employees' in df.columns:
        column_config['employees'] = st.column_config.NumberColumn("Employees")
    if 'industry' in df.columns:
        column_config['industry'] = st.column_config.TextColumn("Industry")
    if 'location' in df.columns:
        column_config['location'] = st.column_config.TextColumn("Location")
    
    st.dataframe(
        df,
        column_config=column_config,
        hide_index=True,
        use_container_width=True
    )
    
    # Export options
    st.subheader("Export Data")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Export to CSV"):
            if save_to_file(data, "leads", "csv"):
                st.success("Data exported successfully to CSV!")
                
    with col2:
        if st.button("Export to JSON"):
            if save_to_file(data, "leads", "json"):
                st.success("Data exported successfully to JSON!")

def render_error(message: str):
    """Render error message"""
    st.error(f"Error: {message}")

def render_success(message: str):
    """Render success message"""
    st.success(message)