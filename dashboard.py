#!/usr/bin/env python3
"""
Mukbang Analysis Dashboard
Interactive dashboard for analyzing mukbang video data
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from datetime import datetime, timedelta
import re
from pathlib import Path
import sys
import io
import base64
import os

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Page configuration
st.set_page_config(
    page_title="Mukbang Analysis Dashboard",
    page_icon="🍜",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        color: #FF6B6B;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
    }
    .metric-value {
        font-size: 2rem;
        font-weight: bold;
    }
    .metric-label {
        font-size: 0.9rem;
        opacity: 0.9;
    }
    .section-header {
        font-size: 1.5rem;
        font-weight: bold;
        color: #2E86AB;
        margin: 2rem 0 1rem 0;
        border-bottom: 2px solid #2E86AB;
        padding-bottom: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_data
def load_data():
    """Load and preprocess the mukbang data"""
    try:
        # Load the new structured data
        df = pd.read_csv('data/youtube_mukbang_20250621_193144.csv')
        
        # Convert duration to minutes for better analysis
        df['duration_minutes'] = df['duration'] / 60
        
        # Convert upload_date to datetime
        df['upload_date'] = pd.to_datetime(df['upload_date'], errors='coerce')
        
        # Extract year and month for time analysis
        df['upload_year'] = df['upload_date'].dt.year
        df['upload_month'] = df['upload_date'].dt.month
        
        # Clean view counts (remove any non-numeric values)
        df['view_count'] = pd.to_numeric(df['view_count'], errors='coerce')
        df['like_count'] = pd.to_numeric(df['like_count'], errors='coerce').fillna(0)
        df['comment_count'] = pd.to_numeric(df['comment_count'], errors='coerce').fillna(0)
        
        # Calculate engagement rate (likes + comments) / views
        df['engagement_rate'] = np.where(
            df['view_count'] > 0,
            ((df['like_count'] + df['comment_count']) / df['view_count'] * 100),
            0
        )
        
        # Extract text features from titles
        df['title_length'] = df['title'].str.len()
        df['word_count'] = df['title'].str.split().str.len()
        df['has_emoji'] = df['title'].str.contains(r'[^\w\s]', regex=True)
        df['has_numbers'] = df['title'].str.contains(r'\d+', regex=True)
        df['has_caps'] = df['title'].str.contains(r'[A-Z]{2,}', regex=True)
        
        # Extract food-related features
        food_keywords = {
            'noodle': ['noodle', 'ramen', 'udon', 'soba', 'pasta'],
            'meat': ['chicken', 'beef', 'pork', 'meat', 'steak', 'burger'],
            'seafood': ['fish', 'shrimp', 'crab', 'lobster', 'sushi'],
            'spicy': ['spicy', 'hot', 'fire', 'chili', 'pepper'],
            'dessert': ['cake', 'ice cream', 'chocolate', 'sweet', 'dessert'],
            'fast_food': ['mcdonalds', 'kfc', 'burger king', 'pizza', 'taco'],
            'korean': ['korean', 'kimchi', 'bulgogi', 'bibimbap'],
            'japanese': ['japanese', 'sushi', 'ramen', 'tempura'],
            'chinese': ['chinese', 'dim sum', 'dumpling', 'wonton']
        }
        
        for category, keywords in food_keywords.items():
            pattern = '|'.join(keywords)
            df[f'has_{category}'] = df['title'].str.contains(pattern, case=False, na=False)
        
        # Extract food-related keywords from titles for basic food type
        food_keywords_basic = ['noodle', 'ramen', 'pizza', 'burger', 'chicken', 'sushi', 'taco', 'pasta', 'rice', 'bread', 'cake', 'ice cream', 'chocolate']
        df['food_type'] = 'Other'
        
        for keyword in food_keywords_basic:
            mask = df['title'].str.contains(keyword, case=False, na=False)
            df.loc[mask, 'food_type'] = keyword.title()
        
        return df
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return pd.DataFrame()

def format_number(num):
    """Format large numbers with K, M, B suffixes"""
    if pd.isna(num):
        return "N/A"
    if num >= 1e9:
        return f"{num/1e9:.1f}B"
    elif num >= 1e6:
        return f"{num/1e6:.1f}M"
    elif num >= 1e3:
        return f"{num/1e3:.1f}K"
    else:
        return f"{int(num)}"

def main():
    # Header
    st.markdown('<h1 class="main-header">🍜 Mukbang Analysis Dashboard</h1>', unsafe_allow_html=True)
    
    # Load data
    df = load_data()
    
    if df.empty:
        st.error("No data found. Please ensure the data file exists.")
        return
    
    # Sidebar filters
    st.sidebar.header("📊 Filters")
    
    # Date range filter
    if not df['upload_date'].isna().all():
        min_date = df['upload_date'].min()
        max_date = df['upload_date'].max()
        
        # Only show date filter if we have valid dates
        if not pd.isna(min_date) and not pd.isna(max_date):
            date_range = st.sidebar.date_input(
                "Upload Date Range",
                value=(min_date, max_date),
                min_value=min_date,
                max_value=max_date
            )
    
    # Duration filter
    duration_range = st.sidebar.slider(
        "Duration (minutes)",
        min_value=float(df['duration_minutes'].min()),
        max_value=float(df['duration_minutes'].max()),
        value=(float(df['duration_minutes'].min()), float(df['duration_minutes'].max()))
    )
    
    # Food type filter
    food_types = ['All'] + sorted(df['food_type'].unique().tolist())
    selected_food = st.sidebar.selectbox("Food Type", food_types)
    
    # Apply filters
    filtered_df = df.copy()
    if selected_food != 'All':
        filtered_df = filtered_df[filtered_df['food_type'] == selected_food]
    
    filtered_df = filtered_df[
        (filtered_df['duration_minutes'] >= duration_range[0]) &
        (filtered_df['duration_minutes'] <= duration_range[1])
    ]
    
    # Main content
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{len(filtered_df)}</div>
            <div class="metric-label">Total Videos</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        avg_views = filtered_df['view_count'].mean()
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{format_number(avg_views)}</div>
            <div class="metric-label">Avg Views</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        avg_duration = filtered_df['duration_minutes'].mean()
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{avg_duration:.1f}m</div>
            <div class="metric-label">Avg Duration</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        avg_engagement = filtered_df['engagement_rate'].mean()
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{avg_engagement:.2f}%</div>
            <div class="metric-label">Avg Engagement</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Charts section
    st.markdown('<h2 class="section-header">📈 Performance Analysis</h2>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Views vs Duration scatter plot
        fig_scatter = px.scatter(
            filtered_df,
            x='duration_minutes',
            y='view_count',
            title='Views vs Duration',
            labels={'duration_minutes': 'Duration (minutes)', 'view_count': 'Views'},
            hover_data=['title', 'creator_name']
        )
        fig_scatter.update_layout(height=400)
        st.plotly_chart(fig_scatter, use_container_width=True)
    
    with col2:
        # Engagement rate distribution
        fig_engagement = px.histogram(
            filtered_df,
            x='engagement_rate',
            title='Engagement Rate Distribution',
            labels={'engagement_rate': 'Engagement Rate (%)'},
            nbins=20
        )
        fig_engagement.update_layout(height=400)
        st.plotly_chart(fig_engagement, use_container_width=True)
    
    # Food type analysis
    st.markdown('<h2 class="section-header">🍽️ Food Type Analysis</h2>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Food type popularity
        food_stats = filtered_df.groupby('food_type').agg({
            'view_count': 'mean',
            'engagement_rate': 'mean',
            'video_id': 'count'
        }).reset_index()
        food_stats.columns = ['Food Type', 'Avg Views', 'Avg Engagement', 'Video Count']
        
        fig_food = px.bar(
            food_stats,
            x='Food Type',
            y='Avg Views',
            title='Average Views by Food Type',
            color='Avg Engagement',
            color_continuous_scale='viridis'
        )
        fig_food.update_layout(height=400)
        st.plotly_chart(fig_food, use_container_width=True)
    
    with col2:
        # Food type count
        food_counts = filtered_df['food_type'].value_counts()
        fig_pie = px.pie(
            values=food_counts.values,
            names=food_counts.index,
            title='Video Distribution by Food Type'
        )
        fig_pie.update_layout(height=400)
        st.plotly_chart(fig_pie, use_container_width=True)
    
    # Top performers
    st.markdown('<h2 class="section-header">🏆 Top Performing Videos</h2>', unsafe_allow_html=True)
    
    # Top by views
    top_views = filtered_df.nlargest(10, 'view_count')[['title', 'creator_name', 'view_count', 'duration_minutes', 'engagement_rate']]
    top_views['view_count_formatted'] = top_views['view_count'].apply(format_number)
    
    st.subheader("Top 10 Videos by Views")
    st.dataframe(
        top_views[['title', 'creator_name', 'view_count_formatted', 'duration_minutes', 'engagement_rate']],
        column_config={
            'title': 'Title',
            'creator_name': 'Creator',
            'view_count_formatted': 'Views',
            'duration_minutes': st.column_config.NumberColumn('Duration (min)', format="%.1f"),
            'engagement_rate': st.column_config.NumberColumn('Engagement (%)', format="%.2f")
        },
        hide_index=True
    )
    
    # Creator analysis
    st.markdown('<h2 class="section-header">👤 Creator Analysis</h2>', unsafe_allow_html=True)
    
    creator_stats = filtered_df.groupby('creator_name').agg({
        'video_id': 'count',
        'view_count': 'mean',
        'engagement_rate': 'mean',
        'duration_minutes': 'mean'
    }).reset_index()
    creator_stats.columns = ['Creator', 'Video Count', 'Avg Views', 'Avg Engagement', 'Avg Duration']
    creator_stats = creator_stats.sort_values('Avg Views', ascending=False)
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Top creators by average views
        top_creators = creator_stats.head(10)
        fig_creators = px.bar(
            top_creators,
            x='Creator',
            y='Avg Views',
            title='Top Creators by Average Views'
        )
        fig_creators.update_layout(height=400, xaxis_tickangle=-45)
        st.plotly_chart(fig_creators, use_container_width=True)
    
    with col2:
        # Creator video count vs engagement
        fig_creator_scatter = px.scatter(
            creator_stats,
            x='Video Count',
            y='Avg Engagement',
            title='Creator Video Count vs Engagement',
            hover_data=['Creator', 'Avg Views']
        )
        fig_creator_scatter.update_layout(height=400)
        st.plotly_chart(fig_creator_scatter, use_container_width=True)
    
    # Insights section
    st.markdown('<h2 class="section-header">💡 Key Insights</h2>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Format date range safely
        min_date = df['upload_date'].min()
        max_date = df['upload_date'].max()
        
        if pd.isna(min_date) or pd.isna(max_date):
            date_range_str = "Date range not available"
        else:
            date_range_str = f"{min_date.strftime('%Y-%m-%d')} to {max_date.strftime('%Y-%m-%d')}"
        
        st.info(f"""
        **📊 Dataset Overview**
        - Total videos analyzed: {len(df)}
        - Date range: {date_range_str}
        - Average video length: {df['duration_minutes'].mean():.1f} minutes
        """)
    
    with col2:
        st.success(f"""
        **🎯 Performance Highlights**
        - Most viewed video: {format_number(df['view_count'].max())} views
        - Highest engagement: {df['engagement_rate'].max():.2f}%
        - Most popular food type: {df['food_type'].mode().iloc[0] if not df['food_type'].mode().empty else 'N/A'}
        """)
    
    with col3:
        st.warning(f"""
        **📈 Trends**
        - Average views per video: {format_number(df['view_count'].mean())}
        - Average engagement rate: {df['engagement_rate'].mean():.2f}%
        - Top creator: {creator_stats.iloc[0]['Creator'] if not creator_stats.empty else 'N/A'}
        """)
    
    # Raw data section
    st.markdown('<h2 class="section-header">📋 Raw Data</h2>', unsafe_allow_html=True)
    
    if st.checkbox("Show raw data"):
        st.dataframe(filtered_df, use_container_width=True)
    
    # Download section
    st.markdown('<h2 class="section-header">💾 Export Data</h2>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        csv = filtered_df.to_csv(index=False)
        st.download_button(
            label="Download filtered data as CSV",
            data=csv,
            file_name=f"mukbang_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )
    
    with col2:
        # Summary statistics
        summary_stats = filtered_df.describe()
        csv_summary = summary_stats.to_csv()
        st.download_button(
            label="Download summary statistics",
            data=csv_summary,
            file_name=f"mukbang_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )

    # --- New Section: Viral vs. Non-Viral Comparison Plots ---
    st.subheader("Viral vs. Non-Viral Comparison")

    viral = df[df['view_count'] >= df['view_count'].quantile(0.9)]
    non_viral = df[df['view_count'] < df['view_count'].quantile(0.9)]

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Median Duration (min)", f"{viral['duration_minutes'].median():.1f} (viral)", delta=f"{non_viral['duration_minutes'].median():.1f} (non-viral)")
        fig = px.box(df, x=["Viral" if v else "Non-Viral" for v in df['view_count'] >= df['view_count'].quantile(0.9)], y='duration_minutes', color=["Viral" if v else "Non-Viral" for v in df['view_count'] >= df['view_count'].quantile(0.9)], points="all", title="Duration Distribution")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.metric("Median Title Length", f"{viral['title'].str.len().median():.0f} (viral)", delta=f"{non_viral['title'].str.len().median():.0f} (non-viral)")
        fig = px.box(df, x=["Viral" if v else "Non-Viral" for v in df['view_count'] >= df['view_count'].quantile(0.9)], y='title_length', color=["Viral" if v else "Non-Viral" for v in df['view_count'] >= df['view_count'].quantile(0.9)], points="all", title="Title Length Distribution")
        st.plotly_chart(fig, use_container_width=True)

    with col3:
        st.metric("Median Engagement Rate", f"{viral['engagement_rate'].median():.2f}% (viral)", delta=f"{non_viral['engagement_rate'].median():.2f}% (non-viral)")
        fig = px.box(df, x=["Viral" if v else "Non-Viral" for v in df['view_count'] >= df['view_count'].quantile(0.9)], y='engagement_rate', color=["Viral" if v else "Non-Viral" for v in df['view_count'] >= df['view_count'].quantile(0.9)], points="all", title="Engagement Rate Distribution")
        st.plotly_chart(fig, use_container_width=True)

    # --- Food Category Heatmap ---
    st.subheader("Food Category Prevalence in Viral vs. Non-Viral Videos")
    food_cols = [col for col in df.columns if col.startswith('has_')]
    food_summary = pd.DataFrame({
        'Viral': viral[food_cols].mean(),
        'Non-Viral': non_viral[food_cols].mean()
    }).T
    st.dataframe(food_summary.style.format("{:.1%}"))
    fig = px.imshow(food_summary, aspect="auto", color_continuous_scale="YlOrRd", labels=dict(x="Food Category", y="Viral Status", color="Prevalence"))
    st.plotly_chart(fig, use_container_width=True)

    # --- Emoji/CAPS/Number Usage ---
    st.subheader("Title Features in Viral vs. Non-Viral Videos")
    feature_cols = ['has_emoji', 'has_caps', 'has_numbers']
    feature_summary = pd.DataFrame({
        'Viral': viral[feature_cols].mean(),
        'Non-Viral': non_viral[feature_cols].mean()
    }).T
    st.dataframe(feature_summary.style.format("{:.1%}"))
    fig = px.imshow(feature_summary, aspect="auto", color_continuous_scale="Blues", labels=dict(x="Title Feature", y="Viral Status", color="Prevalence"))
    st.plotly_chart(fig, use_container_width=True)

    # --- Placeholder for Feature Importance (XGBoost) ---
    st.subheader("Feature Importance for Virality (XGBoost)")
    feature_importance_path = os.path.join('output', 'xgboost_feature_importance.csv')
    if os.path.exists(feature_importance_path):
        fi_df = pd.read_csv(feature_importance_path)
        fig_fi = px.bar(
            fi_df.head(10),
            x='importance',
            y='feature',
            orientation='h',
            title='Top 10 Features for Virality (XGBoost)',
            labels={'importance': 'Importance', 'feature': 'Feature'},
            color='importance',
            color_continuous_scale='blues'
        )
        fig_fi.update_layout(yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig_fi, use_container_width=True)
    else:
        st.info("Feature importance chart will appear here after XGBoost analysis is complete.")

    # --- Downloadable Insights Report ---
    def generate_report(df):
        buf = io.StringIO()
        buf.write("# Mukbang Viral Analysis Report\n\n")
        buf.write(f"**Total videos analyzed:** {len(df)}\n\n")
        buf.write(f"**Viral threshold (top 10%):** {df['view_count'].quantile(0.9):,.0f} views\n\n")
        buf.write("## Key Insights\n")
        buf.write(f"- Median duration (viral): {viral['duration_minutes'].median():.1f} min\n")
        buf.write(f"- Median duration (non-viral): {non_viral['duration_minutes'].median():.1f} min\n")
        buf.write(f"- Median title length (viral): {viral['title_length'].median():.0f}\n")
        buf.write(f"- Median title length (non-viral): {non_viral['title_length'].median():.0f}\n")
        buf.write(f"- Median engagement rate (viral): {viral['engagement_rate'].median():.2f}%\n")
        buf.write(f"- Median engagement rate (non-viral): {non_viral['engagement_rate'].median():.2f}%\n")
        buf.write("\n## Top Food Categories in Viral Videos\n")
        for col in food_cols:
            if viral[col].mean() > 0.1:
                buf.write(f"- {col.replace('has_', '').title()}: {viral[col].mean()*100:.1f}%\n")
        buf.write("\n## Title Features in Viral Videos\n")
        for col in feature_cols:
            buf.write(f"- {col.replace('has_', '').title()}: {viral[col].mean()*100:.1f}%\n")
        return buf.getvalue()

    report_md = generate_report(df)
    b64 = base64.b64encode(report_md.encode()).decode()
    href = f'<a href="data:text/markdown;base64,{b64}" download="mukbang_viral_report.md">📥 Download Insights Report (Markdown)</a>'
    st.markdown(href, unsafe_allow_html=True)

if __name__ == "__main__":
    main() 