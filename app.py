import streamlit as st
import feedparser
import pandas as pd
from datetime import datetime, timedelta
import time

# --- SETUP ---
st.set_page_config(page_title="Persian News Pro", page_icon="📰", layout="wide")

# CSS för mobilanpassning, RTL och vit text på rubriker
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Vazirmatn:wght@400;700&display=swap');
    
    html, body, [class*="css"] { 
        font-family: 'Vazirmatn', sans-serif; 
        direction: rtl; 
        text-align: right; 
    }
    
    .news-card {
        background: #1e2129; 
        padding: 18px; 
        border-radius: 12px;
        border-right: 6px solid #ff4b2b; 
        margin-bottom: 15px;
    }
    
    .news-card h3 { 
        color: #ffffff !important; 
        margin: 10px 0; 
        font-size: 1.15rem;
        font-weight: 700;
        line-height: 1.6;
    }
    
    .source-tag { 
        background: #333; 
        color: #ff4b2b; 
        padding: 3px 10px; 
        border-radius: 6px; 
        font-size: 0.8rem; 
        font-weight: bold;
    }
    
    a { 
        color: #4dabff !important; 
        text-decoration: none; 
        font-weight: bold; 
    }
    
    .stSidebar { direction: rtl; }
    </style>
    """, unsafe_allow_html=True)

# --- NYHETSKÄLLOR (Nu med Iran International) ---
SOURCES = {
    "Iran International": "https://www.iranintl.com/rss/all",
    "BBC Persian": "https://www.bbc.com/persian/index.xml",
    "Radio Farda": "https://www.radiofarda.com/api/z-$qppe_iqm",
    "DW Persian": "https://rss.dw.com/rdf/rss-fa-all",
    "VOA Farsi": "https://ir.voanews.com/api/z-m_ite_q_iq",
    "Euronews": "https://per.euronews.com/rss?format=google-news&level=theme&name=news"
}

@st.cache_data(ttl=300)
def fetch_data():
    entries = []
    for name, url in SOURCES.items():
        try:
            feed = feedparser.parse(url)
            for e in feed.entries:
                # Parsar datumet säkert
                if hasattr(e, 'published_parsed'):
                    dt = datetime.fromtimestamp(time.mktime(e.published_parsed))
                else:
                    dt = datetime.now()
                
                entries.append({
                    "title": e.title,
                    "link": e.link,
                    "source": name,
                    "date": dt
                })
        except:
            continue
    return pd.DataFrame(entries)

# --- UI ---
st.title("Persian News 📰")

with st.sidebar:
    st.header("تنظیمات (Filter)")
    time_choice = st.radio("بازه زمانی (Tid):", ["۱ ساعت اخیر", "۲۴ ساعت اخیر", "۷ روز اخیر"], index=1)
    # Här kan du välja vilka källor som ska visas
    selected_src = st.multiselect("منابع (Källor):", list(SOURCES.keys()), default=list(SOURCES.keys()))

# Hämta data
df = fetch_data()

if not df.empty:
    now = datetime.now()
    if "۱ ساعت" in time_choice: threshold = now - timedelta(hours=1)
    elif "۲۴ ساعت" in time_choice: threshold = now - timedelta(days=1)
    else: threshold = now - timedelta(days=7)

    # Filtrera på tid och källa
    mask = (df['date'] >= threshold) & (df['source'].isin(selected_src))
    df_filtered = df[mask].sort_values(by='date', ascending=False)

    if df_filtered.empty:
        st.info("خبری یافت نشد.")
    else:
        for _, row in df_filtered.iterrows():
            st.markdown(f"""
                <div class="news-card">
                    <div>
                        <span class="source-tag">{row['source']}</span> 
                        <span style="color:#aaa; font-size:0.8rem; margin-right: 10px;">{row['date'].strftime('%H:%M')}</span>
                    </div>
                    <h3>{row['title']}</h3>
                    <a href="{row['link']}" target="_blank">مطالعه خبر ⬅️</a>
                </div>
            """, unsafe_allow_html=True)
else:
    st.error("خطا در بارگذاری اخبار. لطفاً صفحه را رفرش کنید.")
