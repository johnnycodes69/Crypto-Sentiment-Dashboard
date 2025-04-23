import streamlit as st
import snscrape.modules.twitter as sntwitter
import pandas as pd
from textblob import TextBlob
import matplotlib.pyplot as plt
import praw
from datetime import datetime, timedelta

st.set_page_config(page_title="Crypto Sentiment Tracker", layout="wide")

st.title("Social Sentiment Scraper for Twitter Crypto")

#Sidebar date range - default last 7 days
default_start = datetime.now() - timedelta(days=7)
default_end = datetime.today()

start_date, end_date = st.date_input(
    "Select date range for tweets",
    value=(default_start, default_end)
)

#Sidebar Sources
st.sidebar.title("Sources")
source = st.sidebar.selectbox("Select source:", ["Twitter", "Reddit"])

#Sidebar Query
query = st.sidebar.text_input("Enter search term (e.g., $ETH, Solana):", "$ETH")

#Sidebar Limit
limit = st.sidebar.slider("Number of posts", 10, 10000, 10000)

time_filter = st.selectbox(
    "Choose time range for posts",
    ["hour", "day", "week", "month", "year","all"],
    index=1
)


#Reddit API setup
REDDIT_CLIENT_ID = "e5iN6KT-_oBJW7Oz7ahoWQ"
REDDIT_CLIENT_SECRET = "T_dP11nUaZTrY3rV9Ty8ZVdEyw-5fA"
REDDIT_USER_AGENT = "streamlit sentiment app by u/Obvious-Donut-420"


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

#Charts n shit
st.title("Social Sentiment Dashboard")
st.write(f"Analyzing **{query}** from **{source}**...")

if query:
    if source == "Twitter":
        data = scrape_tweets(query, limit, start_date, end_date)
    elif source == "Reddit":
        data = fetch_reddit_posts(query, limit, time_filter)
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