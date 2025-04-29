import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta, timezone
from textblob import TextBlob
import altair as alt


#Sidebar Config
st.sidebar.title("Select Data Source")
source = st.sidebar.selectbox(
    "Select source",
     ["CryptoPanic", "Altcoin Buzz", "Coindesk"]
     )
limit = st.sidebar.slider("Numebr of articles", min_value=1, max_value=50, value=10)
apply_date_filter = st.sidebar.checkbox("Filter by date range")

start_date = end_date = None
if apply_date_filter:
    start_date = st.sidebar.date_input("Start Date", datetime.today() - timedelta(days=7))
    end_date = st.sidebar.date_input("End Date", datetime.today())

# Cryptopanic API setup
CRYPTOPANIC_API_KEY = "161fd6bd2e6af6880bd3a7db2445f0bc1a617ab2"

#Data retrieval functions
def fetch_coindesk_news(limit=10):
    try:
        url = f"https://api.coindesk.com/v1/news?limit={limit}"
        response = requests.get(url)
        response.raise_for_status
        articles = response.json().get("data", [])
        news = []
        for item in articles:
             title = item.get("title") or "No title available"
             date = item.get("published_at", datetime.now(timezone.utc).isoformat())
             url = item.get("url", "")
             news.append({"Title": title, "Date": date, "URL": url})
        return pd.DataFrame(news, columns=["Title", "Date", "URL"])
    except Exception as e:
        st.error(f"Error fetching coindesk news: {e}")
        return pd.DataFrame(columns=["Title","Date","URL"])

def fetch_altcoinbuzz_news(limit=10):
        try:
            url = f"https://altcoinbuzz.io/wp-json/wp/v2/posts?per_page={limit}"
            response = requests.get(url)
            response.raise_for_status()
            articles = response.json()
            news = []
            for item in articles:
                 title = item.get("title", {}).get("rendered", "No title available")
                 date = item.get("date", datetime.now(timezone.utc).isoformat())
                 url = item.get("link", "")
                 news.append({"Title": title, "Date": date, "URL": url})
            return pd.DataFrame(news, columns=["Title", "Date", "URL"])
        except Exception as e:
            st.error(f"Error fetching Altcoinbuzz news: {e}")
            return pd.DataFrame(columns=["Title","Date","URL"])

def fetch_cryptopanic_news(api_key, limit=10):
        try:
            url = f"https://cryptopanic.com/api/v1/posts/?auth_token={api_key}&public=true&currencies=bitcoin&filter=latest"
            response = requests.get(url)
            response.raise_for_status()
            articles = response.json().get("results", [])[:limit]
            news = []
            for item in articles:
                 title = item.get("title") or "No title available"
                 date = item.get("published_at", datetime.now(timezone.utc).isoformat())
                 url = item.get("url", "")
                 news.append({"Title": title, "Date": date, "URL": url})
            return pd.DataFrame(news, columns=["Title", "Date", "URL"])
        except Exception as e:
            st.error(f"Error fetching Cryptopanic news: {e}")
            return pd.DataFrame(columns=["Title", "Date", "URL"])

#Sentiment analysis bit
def add_sentiment_scores(df):
     if "Title" not in df.columns:
          st.warning("No 'Title' column found for sentiment analysis.")
          df["Sentiment"] = []
          return df

     df["Sentiment"] = df["Title"].apply(lambda text: TextBlob(text).sentiment.polarity)
     return df

#Main app logic
st.title("Crypto Sentiment Aggregator")
data = pd.DataFrame()

if source == "CoinDesk":
     data = fetch_coindesk_news(limit)
elif source == "AltcoinBuzz":
     data = fetch_altcoinbuzz_news(limit)
elif source == "CryptoPanic":
     if CRYPTOPANIC_API_KEY:
          data = fetch_cryptopanic_news(CRYPTOPANIC_API_KEY, limit)
     else:
          st.warning("CryptoPanic API key not found. Please set it in Streamlit secrets.")

# Date filter
if not data.empty:
     data["Date"] = pd.to_datetime(data["Date"], errors="coerce")
     data["Date"] = data["Date"].dt.tz_localize(None)

     if apply_date_filter and start_date and end_date:
          start_date = pd.to_datetime(start_date)
          end_date = pd.to_datetime(end_date) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
          data = data[(data["Date"] >= start_date) & (data["Date"] <= end_date)]


data = add_sentiment_scores(data)

# Display results!
if not data.empty:
     st.dataframe(data)
     chart = alt.Chart(data).mark_line(point=True).encode(
          x=alt.X("Date:T", title="Date"),
          y=alt.Y("Sentiment:Q", title="Sentiment Score"),
          tooltip=["Date", "Sentiment", "Title"]
     ).properties(
          title="Sentiment Over Time",
          width=700,
          height=400
     ).interactive()

     st.altair_chart(chart, use_container_width=True)
else:
     st.info("No news available to display.")