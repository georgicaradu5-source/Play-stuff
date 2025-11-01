import os
import tweepy
from dotenv import load_dotenv


def main():
    load_dotenv()
    client = tweepy.Client(
        consumer_key=os.getenv("X_API_KEY"),
        consumer_secret=os.getenv("X_API_SECRET"),
        access_token=os.getenv("X_ACCESS_TOKEN"),
        access_token_secret=os.getenv("X_ACCESS_SECRET"),
    )
    q = '(Power BI OR "Power Platform") lang:en -is:retweet -is:reply'
    r = client.search_recent_tweets(query=q, max_results=10)
    print(len(r.data or []), "hits")


if __name__ == "__main__":
    main()

