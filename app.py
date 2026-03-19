import streamlit as st
import feedparser
import pandas as pd
from datetime import datetime, timedelta
import time

# --- SETUP ---
st.set_page_config(page_title="Persian News", page_icon="📰", layout="wide")

# CSS för mobilanpassning och RTL
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Vazirmatn:wght@400;700&display=swap');
    html, body, [class*="css"] { font-family: 'Vazirmatn', sans-serif; direction: rtl; text-align: right; }
    .news-card {
        background: #1e2129; padding: 15px; border-radius: 12px;
        border-right: 5px solid #ff4b2b; margin-bottom: 15px;
    }
    .source-tag { background: #333; color: #ff4b2b; padding: 2px 8px; border-radius: 5px; font-size: 0.8rem; }
    a { color: #4dabff !important; text-decoration: none; font-weight: bold; }
    /* Fix för mobil-menyn */
    .stSidebar { direction: rtl; }
    </style>
    """, unsafe_allow_html=True)

# --- KÄLLOR ---
SOURCES = {
    "BBC Persian": "https://www.bbc.com/persian/index.xml",
    "Radio Farda": "https://www.radiofarda.com/api/z-$qppe_iqm",
    "DW Persian": "https://rss.dw.com/rdf/rss-fa-all",
    "VOA Farsi": "https://ir.voanews.com/api/z-m_ite_q_iq",
    "Euronews": "https://per.euronews.com/rss?format=google-news&level=theme&name=news"
}

@st.cache_data(ttl=300) # Uppdaterar var 5:e minut
def fetch_data():
    entries = []
    for name, url in SOURCES.items():
        try:
            feed = feedparser.parse(url)
            for e in feed.entries:
                dt = datetime.fromtimestamp(time.mktime(e.published_parsed)) if hasattr(e, 'published_parsed') else datetime.now()
                entries.append({"title": e.title, "link": e.link, "source": name, "date": dt})
        except: continue
    return pd.DataFrame(entries)

# --- UI ---
st.title("Persian News 📰")

# Filter i sidomenyn
with st.sidebar:
    st.header("تنظیمات (Filter)")
    time_choice = st.radio("بازه زمانی (Tid):", ["۱ ساعت اخیر", "۲۴ ساعت اخیر", "۷ روز اخیر"], index=1)
    selected_src = st.multiselect("منابع (Källor):", list(SOURCES.keys()), default=list(SOURCES.keys()))

# Logik för tid
df = fetch_data()
now = datetime.now()
if "۱ ساعت" in time_choice: threshold = now - timedelta(hours=1)
elif "۲۴ ساعت" in time_choice: threshold = now - timedelta(days=1)
else: threshold = now - timedelta(days=7)

df = df[(df['date'] >= threshold) & (df['source'].isin(selected_src))]

# Visa nyheter
if df.empty:
    st.info("خبری یافت نشd (Inga nyheter hittades).")
else:
    for _, row in df.sort_values(by='date', ascending=False).iterrows():
        st.markdown(f"""
            <div class="news-card">
                <span class="source-tag">{row['source']}</span> 
                <span style="color:#888; font-size:0.8rem;">{row['date'].strftime('%H:%M')}</span>
                <h3 style="margin:10px 0; font-size:1.1rem;">{row['title']}</h3>
                <a href="{row['link']}" target="_blank">مطالعه خبر ⬅️</a>
            </div>
        """, unsafe_allow_html=True)
