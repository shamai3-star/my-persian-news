import streamlit as st
import feedparser
import pandas as pd
from datetime import datetime, timedelta
import time
import requests
import io

# --- SETUP ---
st.set_page_config(page_title="Persian News Pro", page_icon="📰", layout="wide")

# CSS (Vit text för rubriker, RTL, snyggare layout)
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Vazirmatn:wght@400;700&display=swap');
    html, body, [class*="css"] { font-family: 'Vazirmatn', sans-serif; direction: rtl; text-align: right; }
    .news-card {
        background: #1e2129; padding: 18px; border-radius: 12px;
        border-right: 6px solid #ff4b2b; margin-bottom: 15px;
    }
    .news-card h3 { color: #ffffff !important; margin: 10px 0; font-size: 1.15rem; font-weight: 700; line-height: 1.6; }
    .source-tag { background: #333; color: #ff4b2b; padding: 3px 10px; border-radius: 6px; font-size: 0.8rem; font-weight: bold; }
    a { color: #4dabff !important; text-decoration: none; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- NYHETSKÄLLOR (Med Google News Proxy för Iran Intl) ---
SOURCES = {
    "Iran International": "https://news.google.com/rss/search?q=site:iranintl.com&hl=fa&gl=IR&ceid=IR:fa",
    "BBC Persian": "https://www.bbc.com/persian/index.xml",
    "Radio Farda": "https://www.radiofarda.com/api/z-$qppe_iqm",
    "DW Persian": "https://rss.dw.com/rdf/rss-fa-all",
    "VOA Farsi": "https://ir.voanews.com/api/z-m_ite_q_iq",
    "Euronews": "https://per.euronews.com/rss?format=google-news&level=theme&name=news"
}

@st.cache_data(ttl=300)
def fetch_data():
    entries = []
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    for name, url in SOURCES.items():
        try:
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                raw_data = io.BytesIO(response.content)
                feed = feedparser.parse(raw_data)
                
                for e in feed.entries:
                    # Datum-hantering
                    if hasattr(e, 'published_parsed'):
                        dt = datetime.fromtimestamp(time.mktime(e.published_parsed))
                    else:
                        dt = datetime.now()
                    
                    # Rensa titeln för Iran Intl (Google News lägger till källan i slutet av titeln)
                    title = e.title
                    if " - " in title:
                        title = title.split(" - ")[0]
                    
                    entries.append({"title": title, "link": e.link, "source": name, "date": dt})
        except:
            continue
    return pd.DataFrame(entries)

# --- UI ---
st.title("Persian News 📰")

with st.sidebar:
    st.header("تنظیمات (Filter)")
    time_choice = st.radio("بازه زمانی (Tid):", ["۱ ساعت اخیر", "۲۴ ساعت اخیر", "۷ روز اخیر"], index=1)
    selected_src = st.multiselect("منابع (Källor):", list(SOURCES.keys()), default=list(SOURCES.keys()))

df = fetch_data()

if not df.empty:
    # Tids-logik (justerat för UTC om servrarna ligger utomlands)
    now = datetime.now()
    if "۱ ساعت" in time_choice: threshold = now - timedelta(hours=1)
    elif "۲۴ ساعت" in time_choice: threshold = now - timedelta(days=1)
    else: threshold = now - timedelta(days=7)

    mask = (df['date'] >= threshold) & (df['source'].isin(selected_src))
    df_filtered = df[mask].sort_values(by='date', ascending=False)

    if df_filtered.empty:
        st.info("خبri یافت نشد در این بازه زمانی (Inga nyheter inom valt tidsintervall).")
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
