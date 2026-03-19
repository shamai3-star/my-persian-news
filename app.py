import streamlit as st
import feedparser
import pandas as pd
from datetime import datetime, timedelta
import time
import requests
from bs4 import BeautifulSoup

# --- SETUP ---
st.set_page_config(page_title="Persian News Pro", page_icon="📡", layout="wide")

# CSS för RTL och vita rubriker
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Vazirmatn:wght@400;700&display=swap');
    html, body, [class*="css"] { font-family: 'Vazirmatn', sans-serif; direction: rtl; text-align: right; }
    .news-card {
        background: #1e2129; padding: 18px; border-radius: 12px;
        border-right: 6px solid #ff4b2b; margin-bottom: 15px;
    }
    .news-card h3 { color: #ffffff !important; margin: 10px 0; font-size: 1.1rem; font-weight: 700; line-height: 1.6; }
    .source-tag { background: #333; color: #ff4b2b; padding: 3px 10px; border-radius: 6px; font-size: 0.8rem; font-weight: bold; }
    .stSidebar { direction: rtl; }
    a { color: #4dabff !important; text-decoration: none; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- FUNKTIONER FÖR DATAMOTTAGNING ---

def fetch_telegram_news():
    items = []
    try:
        url = "https://t.me/s/iranintltv"
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        messages = soup.find_all('div', class_='tgme_widget_message_text')
        
        for msg in messages[:15]:
            text = msg.get_text()
            lines = text.split('\n')
            title = lines[0] if len(lines[0]) > 10 else text[:100] + "..."
            items.append({
                "title": title,
                "link": "https://t.me/iranintltv",
                "source": "Iran International (Telegram)",
                "date": datetime.now() # Telegram webbvy ger inte exakt tid per post i standardformat
            })
    except: pass
    return items

def fetch_rss_news(name, url):
    items = []
    try:
        feed = feedparser.parse(url)
        for e in feed.entries[:15]:
            dt = datetime.fromtimestamp(time.mktime(e.published_parsed)) if hasattr(e, 'published_parsed') else datetime.now()
            items.append({"title": e.title, "link": e.link, "source": name, "date": dt})
    except: pass
    return items

@st.cache_data(ttl=600)
def get_all_news():
    all_data = []
    all_data.extend(fetch_telegram_news())
    
    rss_sources = {
        "BBC Persian": "https://www.bbc.com/persian/index.xml",
        "Radio Farda": "https://www.radiofarda.com/api/z-$qppe_iqm",
        "Independent Persian": "https://www.independentpersian.com/rss.xml",
        "Euronews": "https://per.euronews.com/rss?format=google-news&level=theme&name=news"
    }
    
    for name, url in rss_sources.items():
        all_data.extend(fetch_rss_news(name, url))
        
    return pd.DataFrame(all_data)

# --- UI & FILTRERING ---

st.title("Persian News Live 📡")

# Hämta grunddata
df = get_all_news()

# Sidomeny (Sidebar)
with st.sidebar:
    st.header("تنظیمات (Inställningar)")
    
    # 1. Tidsintervall
    time_choice = st.radio(
        "بازه زمانی (Tidsperiod):", 
        ["۱ ساعت اخیر (1h)", "۲۴ ساعت اخیر (24h)", "۷ روز اخیر (7d)"], 
        index=1
    )
    
    # 2. Källväljare
    all_sources = df['source'].unique().tolist() if not df.empty else []
    selected_src = st.multiselect("منابع خبری (Källor):", all_sources, default=all_sources)
    
    # 3. Sökfält
    search_query = st.text_input("جستجو (Sök i rubriker):", "")

    st.markdown("---")
    if st.button("به‌روزرسانی محتوا (Refresh)"):
        st.cache_data.clear()
        st.rerun()

# Logik för filtrering
if not df.empty:
    now = datetime.now()
    if "۱ ساعت" in time_choice: threshold = now - timedelta(hours=1)
    elif "۲۴ ساعت" in time_choice: threshold = now - timedelta(days=1)
    else: threshold = now - timedelta(days=7)

    # Filtrera på tid, källa och sökord
    mask = (df['date'] >= threshold) & (df['source'].isin(selected_src))
    if search_query:
        mask = mask & (df['title'].str.contains(search_query, case=False, na=False))
        
    df_filtered = df[mask].sort_values(by='date', ascending=False)

    # Visa resultatet
    if df_filtered.empty:
        st.warning("خبری یافت نشد.")
    else:
        for _, row in df_filtered.iterrows():
            st.markdown(f"""
                <div class="news-card">
                    <div>
                        <span class="source-tag">{row['source']}</span>
                        <span style="color:#888; font-size:0.75rem; margin-right:10px;">
                            {row['date'].strftime('%H:%M')}
                        </span>
                    </div>
                    <h3>{row['title']}</h3>
                    <a href="{row['link']}" target="_blank">مشاهده در منبع ⬅️</a>
                </div>
            """, unsafe_allow_html=True)
else:
    st.error("خطا در دریافت اطلاعات.")
