import streamlit as st
import feedparser
import pandas as pd
from datetime import datetime, timedelta
import time
import requests
from bs4 import BeautifulSoup
import re

# --- SETUP ---
st.set_page_config(page_title="Persian News Pro", page_icon="📡", layout="wide")

# CSS (Håller allt snyggt, RTL och vita rubriker)
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
    .time-tag { color: #888; font-size: 0.75rem; margin-right: 10px; }
    a { color: #4dabff !important; text-decoration: none; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- FUNKTION: HÄMTA FRÅN TELEGRAM (Iran Intl) ---
def fetch_telegram_news():
    items = []
    try:
        # Vi läser den publika webbvyn av Iran Internationals Telegram-kanal
        url = "https://t.me/s/iranintltv"
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Telegram lagrar varje inlägg i en div med klassen 'tgme_widget_message_wrap'
        messages = soup.find_all('div', class_='tgme_widget_message_text')
        
        for msg in messages[:15]: # Hämta de 15 senaste
            text = msg.get_text()
            # Vi tar första raden som rubrik om den är kort, annars kapar vi den
            lines = text.split('\n')
            title = lines[0] if len(lines[0]) > 10 else text[:100] + "..."
            
            # Telegram-länkar är interna, så vi länkar till kanalen generellt
            items.append({
                "title": title,
                "link": "https://t.me/iranintltv",
                "source": "Iran International (Telegram)",
                "date": datetime.now() # Telegram webb-vy ger sällan exakta datum per post i RSS-format
            })
    except:
        pass
    return items

# --- FUNKTION: HÄMTA RSS (Övriga) ---
def fetch_rss_news(name, url):
    items = []
    try:
        feed = feedparser.parse(url)
        for e in feed.entries[:10]:
            dt = datetime.fromtimestamp(time.mktime(e.published_parsed)) if hasattr(e, 'published_parsed') else datetime.now()
            items.append({"title": e.title, "link": e.link, "source": name, "date": dt})
    except:
        pass
    return items

# --- HUVUDLOGIK ---
@st.cache_data(ttl=600)
def get_all_news():
    all_news = []
    
    # 1. Hämta Telegram-nyheter först (Lösningen för Iran Intl)
    all_news.extend(fetch_telegram_news())
    
    # 2. Hämta övriga källor
    sources = {
        "BBC Persian": "https://www.bbc.com/persian/index.xml",
        "Radio Farda": "https://www.radiofarda.com/api/z-$qppe_iqm",
        "Independent Persian": "https://www.independentpersian.com/rss.xml",
        "Euronews": "https://per.euronews.com/rss?format=google-news&level=theme&name=news"
    }
    
    for name, url in sources.items():
        all_news.extend(fetch_rss_news(name, url))
        
    return pd.DataFrame(all_news)

# --- UI ---
st.title("Persian News Live 📡")

with st.sidebar:
    st.header("تنظیمات")
    if st.button("به‌روزرسانی محتوا (Refresh)"):
        st.cache_data.clear()
        st.rerun()

df = get_all_news()

if not df.empty:
    # Eftersom Telegram-datumen är "nu", sorterar vi men prioriterar källor
    for _, row in df.iterrows():
        st.markdown(f"""
            <div class="news-card">
                <div>
                    <span class="source-tag">{row['source']}</span>
                </div>
                <h3>{row['title']}</h3>
                <a href="{row['link']}" target="_blank">مشاهده در منبع ⬅️</a>
            </div>
        """, unsafe_allow_html=True)
else:
    st.error("خطا در دریافت اخبار.")
