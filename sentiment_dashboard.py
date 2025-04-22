import streamlit as st
import snscrape.modules.twitter as sntwitter
import pandas as pd
from textblob import TextBlob
import matplotlib.pyplot as plt
import praw

st.set_page_config(page_title="Crypto Sentiment Tracker", layout="wide")

st.title("Social Sentiment Scraper for Twitter Crypto")

#Sidebar Sources
st.sidebar.title("Sources")
source = st.sidebar.selectbox("Select source:", ["Twitter", "Reddit"])

#Sidebar Query
query = st.sidebar.text_input("Enter search term (e.g., $ETH, Solana):", "$ETH")

#Sidebar Limit
limit = st.sidebar.slider("Number of posts", 10, 200, 50)

#Reddit API setup
REDDIT_CLIENT_ID = "your_client_id"
REDDIT_CLIENT_SECRET = "your_client_secret"
REDDIT_USER_AGENT = "your_user_agent"

def analyze_sentiment(text):
    blob = TextBlob(text)
    polarity = blob.sentiment.polarity
    sentiment = "Positive" if polarity > 0 else "Negative" if polarity < 0 else "Neutral"
    return sentiment

#Tweet Scraper
def scrape_tweets(query, limit=100):
    tweets = []
    try:
        for i, tweet in enumerate(sntwitter.TwitterSearchScraper(query).get_items()):
            if i >= limit:
                break
            tweets.append({
                "Date": tweet.date,
                "User": tweet.user.username,
                 "Content": tweet.content
                 })
    except Exception as e:
        st.error(f"Error scraping tweets: {e}")
    return pd.DataFrame(columns=["Date", "User", "Content"])

    df = pd.DataFrame(tweets)
    df["Sentiment"] = df["Content"].apply(analyze_sentiment)
    return df

#Reddit post scraper
def fetch_reddit_posts(query, limit=100):
    try:
        reddit = praw.Reddit(
            client_id=REDDIT_CLIENT_ID,
            client_secret=REDDIT_CLIENT_SECRET,
            user_agent=REDDIT_USER_AGENT
        )
        subreddit = reddit.subreddit("all")
        results = []

        for post in subreddit.search(query, sort="relevance", time_filter="day, limit=limit"):
            text = f"{post.title} {post.selftext}"
            results.append({
                "Date": pd.to_datetime(post.created_utc, unit='s'),
                "User": post.author.name if post.author else "[deleted]",
                "Content": text
            })

            df = pd.DataFrame
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
        data = scrape_tweets(query, limit)
    elif source == "Reddit":
        data = fetch_reddit_posts(query, limit)
    else:
        data = pd.DataFrame()
    
    if not data.empty:
        sentiment_counts = data["Sentiment"].value_counts()
        st.bar_chart(sentiment_counts)
        st.dataframe(data)
    else:
        st.info("No data available. Try a different keyword or reduce the limit.")
else:
    st.warning("Please enter a query.")