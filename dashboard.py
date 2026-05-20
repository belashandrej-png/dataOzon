import streamlit as st
import pandas as pd
import plotly.express as px
import os
from collections import Counter
import re
from wordcloud import WordCloud
import matplotlib.pyplot as plt

st.set_page_config(page_title="Mimovrste Analytics", layout="wide", page_icon="📊")

st.title("💎 Mimovrste Analytics Platform")
st.markdown("Price analysis, brands and categories")
st.markdown("---")

@st.cache_data
def load_data():
    try:
        file_path = 'O:/extracted/mimodump-dataset.csv'
        if not os.path.exists(file_path):
            st.error("File not found!")
            return None
        df = pd.read_csv(file_path, nrows=50000, sep=';', low_memory=False, encoding='utf-8')
        
        numeric_cols = ['price', 'current_price', 'review_count', 'review_stars']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        return df
    except Exception as e:
        st.error(f"Error: {e}")
        return None

df = load_data()

if df is not None:
    st.success(f"✅ Loaded {len(df):,} items")
    
    # Sidebar filters
    st.sidebar.header("Filters")
    if 'brand_name' in df.columns:
        brands = df['brand_name'].value_counts().head(20).index
        selected_brands = st.sidebar.multiselect("Brands:", options=brands, default=list(brands[:5]))
        if selected_brands:
            df = df[df['brand_name'].isin(selected_brands)]

    if 'price' in df.columns:
        valid_prices = df['price'].dropna()
        if len(valid_prices) > 0:
            price_range = st.sidebar.slider("Price range:", min_value=float(valid_prices.min()), max_value=float(valid_prices.max()), value=(float(valid_prices.min()), min(float(valid_prices.max()), 500.0)))
            df = df[(df['price'] >= price_range[0]) & (df['price'] <= price_range[1])]

    # Metrics
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Items", f"{len(df):,}")
    if 'brand_name' in df.columns:
        col2.metric("Brands", df['brand_name'].nunique())
    if 'price' in df.columns:
        col3.metric("Avg Price", f"{df['price'].mean():.2f} EUR")
    if 'review_stars' in df.columns:
        col4.metric("Rating", f"{df['review_stars'].mean():.2f}/5")

    st.markdown("---")

    # GRAPHS 1
    col_a, col_b = st.columns(2)
    
    with col_a:
        if 'category_name' in df.columns:
            st.subheader("📊 Categories Structure")
            cat_counts = df['category_name'].value_counts().head(15).reset_index()
            cat_counts.columns = ['Category', 'Count']
            fig = px.treemap(cat_counts, path=['Category'], values='Count', color='Count', color_continuous_scale='Viridis')
            st.plotly_chart(fig, use_container_width=True)

    with col_b:
        if 'price' in df.columns:
            st.subheader("💸 Price Distribution")
            df_clean = df[(df['price'] > 0) & (df['price'] < 500)].dropna(subset=['price'])
            fig = px.histogram(df_clean, x='price', nbins=50, color_discrete_sequence=['#FF6B6B'])
            st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    st.subheader("🔍 Detailed Analytics")
    
    c1, c2 = st.columns(2)
    
    with c1:
        if 'brand_name' in df.columns:
            st.subheader("🏆 Top Brands")
            brand_counts = df['brand_name'].value_counts().head(10).reset_index()
            brand_counts.columns = ['Brand', 'Count']
            fig = px.bar(brand_counts, x='Count', y='Brand', orientation='h', color='Count', color_continuous_scale='Rainbow')
            st.plotly_chart(fig, use_container_width=True)

    with c2:
        if 'category_name' in df.columns and 'price' in df.columns:
            st.subheader("📉 Prices by Category")
            top_cats = df['category_name'].value_counts().head(5).index
            df_box = df[df['category_name'].isin(top_cats)].dropna(subset=['price'])
            fig = px.box(df_box, x='category_name', y='price', color='category_name')
            st.plotly_chart(fig, use_container_width=True)

    # NEW: WORD CLOUD
    st.markdown("---")
    st.subheader("🔑 Word Cloud - Product Names")
    
    if 'name' in df.columns:
        st.markdown("**Most frequent words in product names:**")
        
        # Combine all product names
        all_text = ' '.join(df['name'].dropna().astype(str))
        
        # Clean text
        all_text = all_text.lower()
        words = re.findall(r'\b[a-zA-Zа-яА-ЯёЁ0-9]{3,}\b', all_text)
        
        # Remove stop words
        stop_words = {
            'the', 'and', 'for', 'with', 'from', 'that', 'this', 'which', 'have', 'has',
            'и', 'в', 'на', 'для', 'как', 'по', 'о', 'с', 'к', 'за', 'под', 'при', 'без', 'над', 'перед',
            'это', 'все', 'или', 'но', 'не', 'ни', 'бы', 'же', 'ли', 'так', 'то', 'а', 'у', 'из', 'до', 'от'
        }
        words = [w for w in words if w not in stop_words and len(w) > 2]
        
        # Create word cloud
        word_freq = Counter(words)
        
        col_wc1, col_wc2 = st.columns([2, 1])
        
        with col_wc1:
            st.subheader("Word Cloud Visualization")
            
            # Generate word cloud
            wc = WordCloud(
                width=1200, 
                height=600, 
                background_color='white',
                colormap='viridis',
                max_words=200,
                min_font_size=5,
                max_font_size=150,
                random_state=42,
                contour_width=1,
                contour_color='steelblue'
            ).generate_from_frequencies(word_freq)
            
            # Display
            fig, ax = plt.subplots(figsize=(12, 6))
            ax.imshow(wc, interpolation='bilinear')
            ax.axis('off')
            plt.tight_layout()
            st.pyplot(fig)
        
        with col_wc2:
            st.subheader("Top 30 Words")
            top_words = word_freq.most_common(30)
            top_df = pd.DataFrame(top_words, columns=['Word', 'Frequency'])
            
            # Bar chart
            fig_bar = px.bar(top_df, x='Frequency', y='Word', orientation='h',
                            color='Frequency', color_continuous_scale='Plasma')
            fig_bar.update_layout(yaxis={'categoryorder': 'total ascending'})
            st.plotly_chart(fig_bar, use_container_width=True)
            
            # Stats
            st.metric("Total Words", f"{len(words):,}")
            st.metric("Unique Words", f"{len(word_freq):,}")

    st.markdown("---")
    st.subheader("📋 Data Preview")
    cols_to_show = ['name', 'price', 'current_price', 'brand_name', 'category_name']
    available_cols = [c for c in cols_to_show if c in df.columns]
    st.dataframe(df[available_cols].head(50), use_container_width=True)

else:
    st.warning("⚠️ No data loaded")
