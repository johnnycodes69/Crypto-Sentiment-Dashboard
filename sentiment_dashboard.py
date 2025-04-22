import streamlit as lit
import snscrape.modules.twitter as sntwitter
import pandas as pd
from textblob import TextBlob
import matplotlib.pyplot as plt

st.set_page_config(page_title="Crypto Sentiment Tracker", layout="wide")

st.title("Social Sentiment Scraper for Twitter Crypto")

#Inputs for the sidebar
query = st.text_input("Enter search term (e.g., $ETH, Solana, #Bitcoin):", "$ETH")
tweet_limit = st.slider("Number of tweets", min_value=50, max_value=1000, step=50, value=200)

@st.cache.data
def scrape_tweets(query, limit):
    tweets = []
    for i, tweet in enumerate(sntwitter.TwitterSearchScraper(query).get_items()):
        if i >= limit:
            break
        tweets.append([tweet.date, tweet.content])
    df = pd.DataFrame(tweets, columns=["Date", "Tweet"])
    return df

#Sentiment analysis function
def get_sentiment(text):
    return TextBlob(text).sentiment.polarity

if query:
    st.info(f"Scraping tweets for '{query}'")
    df = scrape_tweets(query, tweet_limit)
    df["Sentiment"] = df["Tweet"].apply(get_sentiment)
    df["Date"] = pd.to_datetime(df["Date"])

    #Sample tweets
    with st.expander("Sentiment Distribution"):
        st.dataframe(df.head(10))
    
    #Histogram!
    st.subheader("Sentiment Distribution")
    fig, ax = plt.subplots()
    ax.hist(df["Sentiment"], bins=30, color="purple", alpha=0.7)
    ax.set_xlabel("Polarity")
    ax.set_ylabel("Frequency")
    ax.set_title("Sentiment Histogram")
    st.pyplot(fig)

    #AVG over time
    df.set_index("Date", inplace=True)
    df_resampled = df["Sentiment"].resamepl("H").mean()
    st.subheader("Sentiment Over Time")
    st.line_chart(df_resampled)

    st.success("Analysis complete!")