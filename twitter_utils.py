import tweepy
import time
import schedule
from io import BytesIO
import requests
import base64
import logging
import os

# Basic logging setup
logging.basicConfig(filename='scheduled_tweets.log', level=logging.ERROR)

def get_twitter_conn_v1(api_key: str, api_secret: str, access_token: str, access_token_secret: str) -> tweepy.API:
    """Get Twitter connection using API v1.1."""
    auth = tweepy.OAuthHandler(api_key, api_secret)
    auth.set_access_token(access_token, access_token_secret)
    return tweepy.API(auth)

def get_twitter_conn_v2(api_key: str, api_secret: str, access_token: str, access_token_secret: str) -> tweepy.Client:
    """Get Twitter connection using API v2."""
    return tweepy.Client(consumer_key=api_key, consumer_secret=api_secret, access_token=access_token, access_token_secret=access_token_secret)

def post_tweet(api_key: str, api_secret: str, access_token: str, access_token_secret: str, content: str, image_path: str = None, image_url: str = None):
    """Post a tweet with optional image attachment."""
    client_v1 = get_twitter_conn_v1(api_key, api_secret, access_token, access_token_secret)
    client_v2 = get_twitter_conn_v2(api_key, api_secret, access_token, access_token_secret)

    media_id = None
    if image_path or image_url:
        try:
            if image_path:  # If image is a local file
                with open(image_path, 'rb') as image_file:
                    media = client_v1.media_upload(filename="image.png", file=image_file)
            else:  # If image is a URL
                response = requests.get(image_url)
                media = client_v1.media_upload(filename="image.png", file=BytesIO(response.content))
            media_id = media.media_id
        except Exception as e:
            logging.error(f"Error uploading image: {e}")

    try:
        # Post the tweet
        client_v2.create_tweet(text=content, media_ids=[media_id] if media_id else None)
    except Exception as e:
        logging.error(f"Error posting tweet: {e}")