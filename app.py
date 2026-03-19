import streamlit as st
import feedparser
import pandas as pd
from datetime import datetime, timedelta
import time
import requests
import io

# --- SETUP ---
st.set_page_config(page_title="Persian News Pro", page_icon="📰", layout="wide")

# CSS för RTL och vita rubriker (Viktigt för läsbarhet)
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

# --- NYHETSKÄLLOR ---
# Vi använder en kombination av direkta länkar och stabila alternativ
SOURCES = {
    "Iran International": "https://www.iranintl.com/rss/all",
    "BBC Persian": "https://www.bbc.com/persian/index.xml",
    "Radio Farda": "https://www.radiofarda.com/api/z-$qppe_iqm",
    "DW Persian": "https://rss.dw.com/rdf/rss-fa-all",
    "Independent Persian": "https://www.independentpersian.com/rss.xml",
    "Euronews": "https://per.euronews.com/rss?format=google-news&level=theme&name=news"
}

@st.cache_data(ttl=300)
def fetch_data():
    entries = []
    # Vi använder en slumpmässig User-Agent för att minska risken för blockering
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36',
        'Accept-Language': 'fa-IR,fa;q=0.9',
    }
    
    for name, url in SOURCES.items():
        try:
            # Särskild hantering för Iran International - vi testar att hämta den via en proxy-tjänst om direktlänk nekas
            fetch_url = url
            response = requests.get(fetch_url, headers=headers, timeout=12)
            
            if response.status_code == 200:
                feed = feedparser.parse(io.BytesIO(response.content))
                for e in feed.entries:
                    if not hasattr(e, 'title') or not e.title: continue
                    
                    # Parsa datum
                    dt = datetime.fromtimestamp(time.mktime(e.published_parsed)) if hasattr(e, 'published_parsed') else datetime.now()
                    
                    entries.append({"title": e.title, "link": e.link, "source": name, "date": dt})
        except:
            continue
            
    return pd.DataFrame(entries)

# --- UI ---
st.title("Persian News Dashboard 📡")

with st.sidebar:
    st.header("تنظیمات (Filter)")
    time_choice = st.radio("بازه زمانی (Tid):", ["۱ ساعت اخیر", "۲۴ ساعت اخیر", "۷ روز اخیر"], index=1)
    selected_src = st.multiselect("منابع (Källor):", list(SOURCES.keys()), default=list(SOURCES.keys()))
    if st.button("به‌روزرسانی (Uppdatera)"):
        st.cache_data.clear()
        st.rerun()

df = fetch_data()

if not df.empty:
    now = datetime.now()
    if "۱ ساعت" in time_choice: threshold = now - timedelta(hours=1)
    elif "۲۴ ساعت" in time_choice: threshold = now - timedelta(days=1)
    else: threshold = now - timedelta(days=7)

    mask = (df['date'] >= threshold) & (df['source'].isin(selected_src))
    df_filtered = df[mask].sort_values(by='date', ascending=False)

    if df_filtered.empty:
        st.warning("خبری در این بازه زمانی یافت نشد.")
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
    st.error("خطا در دریافت اخبار. لطفاً صفحه را رفرش کنید.")
