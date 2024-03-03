import twitter_utils
import twitter_filter
import os
import pandas as pd
import requests
import os
from PIL import Image
from io import BytesIO
import openai

from dotenv import load_dotenv
load_dotenv()


# Example usage:
# Assuming the CSV is accessible via the given URL. If the CSV is stored locally or the format is different, adjustments may be needed.
url = 'https://raw.githubusercontent.com/DanielTea/control-f-github-trending-analysis/main/trending_repositories_summary.csv'
twitter_filter.fetch_and_filter_csv(url)

# Example usage
api_key = os.getenv("X_API_KEY")
api_secret = os.getenv("X_API_SECRET")
access_token = os.getenv("X_ACCESS_TOKEN")
access_token_secret = os.getenv("X_ACCESS_TOKEN_SECRET")
openai_api_key = os.getenv("OPENAI_API_KEY")
tweet_content = 'This is a test tweet.'
image_path = './image.png'  # Use None if no image from local path
image_url = 'http://example.com/image.png'  # Use None if no image from URL


# Load the filtered CSV file
df = pd.read_csv('./filtered_repositories_summary.csv')

for index, row in df.iterrows():
    if not row['Tweet-Send']:

        tweet_content = f"🤖 {row['Blog-Title']}\n\n Github Repository -> {row['Repository-Link']}\n\n Follow Us -> www.controlf.io"
        image_url = None

        image_links = eval(row['Image-Links'])
        image_url = image_links[0]

        if image_url:
            client = openai.OpenAI(api_key=openai_api_key)

                # Classify the GitHub project
            blog_hashtags = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You create 2-3 short hastags for this title, nothing else no comments or any other text. Don't enumerate the hastags just all of them in one line. Put max 1-2 words together."},
                    {"role": "user", "content": row['Blog-Title']}
                ]
            )
            hashtags = blog_hashtags.choices[0].message.content
            tweet_content =  tweet_content+f"\n\n{hashtags}"

            print(image_url)

            if len(tweet_content)> 250:
                tweet_content = f"🤖 {row['Blog-Title']}\n\n Github Repository -> {row['Repository-Link']}\n\n Follow Us -> www.controlf.io"

            response = requests.get(image_url)
            if response.status_code == 200:
                image_data = BytesIO(response.content)
                image = Image.open(image_data)

                image_size = len(response.content)
                print(image_size)
                if image_size > 5 * 1024 * 1024:  # Check if image is larger than 5mb
                    image.save(image_path, optimize=True, quality=85)  # Compress the image
                    image_url = None
                else:
                    image_path = None


                twitter_utils.post_tweet(
                    api_key=api_key, 
                    api_secret=api_secret, 
                    access_token=access_token, 
                    access_token_secret=access_token_secret, 
                    content=tweet_content, 
                    image_path=image_path, 
                    image_url=image_url
                )
                

            else:
                print("Failed to download image from URL")
        else:
            video_link = row["Video-Links"].split(";")[0]

            tweet_content = f"🤖 {row['Blog-Title']}\n\n Follow Us-> www.controlf.io \n\n Github Repository-> {row['Repository-Link']}\n\n YT-Video-> {video_link}"

            client = openai.OpenAI(api_key=openai_api_key)

                # Classify the GitHub project
            blog_hashtags = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You create 2-3 short hastags for this title, nothing else no comments or any other text. Don't enumerate the hastags just all of them in one line. Put max 1-2 words together."},
                    {"role": "user", "content": row['Blog-Title']}
                ]
            )
            hashtags = blog_hashtags.choices[0].message.content
            tweet_content =  tweet_content+f"\n\n{hashtags}"

            if len(tweet_content)> 250:
                tweet_content = f"🤖 {row['Blog-Title']}\n\n Github Repository -> {row['Repository-Link']}\n\n Follow Us -> www.controlf.io \n\n YT-Video-> {video_link}"

            if len(tweet_content)> 250:
                tweet_content = f"🤖 {row['Blog-Title']}\n\n Github Repository -> {row['Repository-Link']}\n\n YT-Video-> {video_link}"

            print(len(tweet_content))

            twitter_utils.post_tweet(
                    api_key=api_key, 
                    api_secret=api_secret, 
                    access_token=access_token, 
                    access_token_secret=access_token_secret, 
                    content=tweet_content, 
                    image_path=None, 
                    image_url=None
                )

        df.at[index, 'Tweet-Send'] = True

# Save the updated DataFrame back to the CSV file
df.to_csv('./filtered_repositories_summary.csv', index=False)