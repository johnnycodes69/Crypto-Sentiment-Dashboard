import streamlit as st
import snscrape.modules.twitter as sntwitter
import pandas as pd
from textblob import TextBlob
import matplotlib.pyplot as plt
import praw
from datetime import datetime, timedelta
import requests

st.set_page_config(page_title="Crypto Sentiment Tracker", layout="wide")

st.title("Social Sentiment Scraper for Crypto")

#Sidebar Sources
st.sidebar.title("Select Data Source")
source = st.sidebar.selectbox(
    "Select source",
     ["Twitter", "Reddit", "Crypto News"]
     )

#Sidebar date range - default last 7 days
default_start = datetime.now() - timedelta(days=7)
default_end = datetime.today()

start_date, end_date = st.date_input(
    "Select date range for tweets",
    value=(default_start, default_end)
)

#Sidebar Query
query = st.sidebar.text_input("Enter search term (e.g., $ETH, Solana):", "Ethereum")

#Sidebar Limit
limit = st.sidebar.slider("Number of posts", 1, 100, 15)

time_filter = st.selectbox(
    "Choose time range for posts",
    ["hour", "day", "week", "month", "year","all"],
    index=1
)

#Reddit API setup
REDDIT_CLIENT_ID = "e5iN6KT-_oBJW7Oz7ahoWQ"
REDDIT_CLIENT_SECRET = "T_dP11nUaZTrY3rV9Ty8ZVdEyw-5fA"
REDDIT_USER_AGENT = "streamlit sentiment app by u/Obvious-Donut-420"

#Cryptopanic API setup
CRYPTOPANIC_API_KEY = "161fd6bd2e6af6880bd3a7db2445f0bc1a617ab2"

def analyze_sentiment(text):
    blob = TextBlob(text)
    polarity = blob.sentiment.polarity
    sentiment = "Positive" if polarity > 0 else "Negative" if polarity < 0 else "Neutral"
    return sentiment

#Tweet Scraper
def scrape_tweets(query, limit=100, start_date=None, end_date=None):
    try:
        date_filter = ""
        if start_date:
            date_filter += f" since:{start_date.strftime('%Y-%m-%d')}"
        if end_date:
            end_inclusive = end_date + timedelta(days=1)
            date_filter += f" until:{end_inclusive.strftime('%Y-%m-%d')}"
    
        full_query = f"{query} lang:en{date_filter}"
        tweets = []
        for i, tweet in enumerate(sntwitter.TwitterSearchScraper(full_query).get_items()):
            if i >= limit:
                break
        tweets.append({
            "Date": tweet.date,
            "User": tweet.user.username,
            "Content": tweet.content
        })
    
    except Exception as e:
        st.error(f"Error fetching tweets: {e}")
        return pd.DataFrame(columns=["Date", "User", "Content", "Sentiment"])    
    
    df = pd.DataFrame(tweets)
    if df.empty:
        return df

    df["Sentiment"] = df["Content"].apply(analyze_sentiment)
    return df
  

#Reddit post scraper
def fetch_reddit_posts(query, limit=100, time_filter="day"):
    try:
        reddit = praw.Reddit(
            client_id=REDDIT_CLIENT_ID,
            client_secret=REDDIT_CLIENT_SECRET,
            user_agent=REDDIT_USER_AGENT
        )
        subreddit = reddit.subreddit("all")
        results = []

        for post in subreddit.search(query, sort="relevance", time_filter=time_filter, limit=limit):
            text = f"{post.title} {post.selftext}"
            results.append({
                "Date": pd.to_datetime(post.created_utc, unit='s'),
                "User": post.author.name if post.author else "[deleted]",
                "Content": text
            })

            df = pd.DataFrame(results)
            if df.empty:
                return df
            
            df["Sentiment"] = df["Content"].apply(analyze_sentiment)
            return df
    
    except Exception as e:
        st.error(f"Error fetching Reddit posts: {e}")
        return pd.DataFrame(columns=["Date", "User", "Content", "Sentiment"])

#Setup CryptoPanic scraper
def fetch_crypto_news(query="", limit=100):
    try:
        url = "https://cryptopanic.com/api/v1/posts/"
        params = {
            "auth_token": CRYPTOPANIC_API_KEY,
            "currencies": query.lower(),
            "public": True
        }

        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        news = []
        for item in data.get("results", [])[:limit]:
            if item is None:
                continue #SKIP null or empty results
            title = item.get("title", "No title")
            url = item.get("url", "")
            domain = item.get("domain","CryptoPanic")
            published = item.get("published_at","")

            content = f"{title} - {url}" if url else title

            news.append({
                "Date": item["published_at"],
                "User": item.get("domain", "Cryptopanic"),
                "Content": item["title"] + " - " + (item.get("url") or "")
            })

        df = pd.DataFrame(news)
        if df.empty:
            return df
        
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
        df.dropna(subset=["Date"], inplace=True)
        df["Sentiment"] = df["Content"].apply(analyze_sentiment)
        return df

    except Exception as e:
        st.error(f"Error fetching CryptoPanic news: {e}")
        return pd.DataFrame(columns=["Date", "User", "Content", "Sentiment"])

#Charts n shit
st.title("Social Sentiment Dashboard")
st.write(f"Analyzing **{query}** from **{source}**...")

if query:
    if source == "Twitter":
        data = scrape_tweets(query, limit, start_date, end_date)
    elif source == "Reddit":
        data = fetch_reddit_posts(query, limit, time_filter)
    elif source == "Crypto News":
        data = fetch_crypto_news(query, limit)
    else:
        data = pd.DataFrame()
    
    if not data.empty:
        st.success(f"Retrieved {len(data)} posts from {source}.")
        sentiment_counts = data["Sentiment"].value_counts()
        st.bar_chart(sentiment_counts)
        st.dataframe(data)
    else:
        st.info("No data available. Try a different keyword or reduce the limit.")
else:
    st.warning("Please enter a query.")