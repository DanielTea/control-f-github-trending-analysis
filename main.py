import requests
from bs4 import BeautifulSoup
import os
import openai
# openai.api_base = "http://localhost:4891/v1"

import csv
from datetime import datetime
import re
import argparse
import json
from datetime import datetime, timedelta


def fetch_trending_repositories(url = 'https://github.com/trending/python?since=daylie'):
    # URL of the trending Python repositories on GitHub
    # Send a request to the URL
    response = requests.get(url)

    # Parse the HTML content of the page
    soup = BeautifulSoup(response.text, 'html.parser')

    # Find all elements containing repository links, adjusting for the provided structure
    repo_elements = soup.find_all('h2', class_='h3 lh-condensed')

    repository_links = []
    stars = []
    # Extract and print the URLs of the repositories
    for repo_element in repo_elements:
        a_tag = repo_element.find('a')
        repo_url = 'https://github.com' + a_tag['href']
        print(repo_url)
        repository_links.append(repo_url)

    repo_elements = soup.find_all('article', class_='Box-row')

    for repo_element in repo_elements:
        # Extract repository URL
        a_tag = repo_element.find('a', href=True)
        repo_url = 'https://github.com' + a_tag['href']

        # Find the element with the star count for this week or today
        # Assuming the text is directly within an element that can be identified
        # The actual class or structure might vary and needs to be updated according to the current GitHub HTML structure
        star_info = repo_element.find(lambda tag: tag.name == "span" and "stars this week" in tag.text or "stars today" in tag.text)
        if star_info:
            star_count_text = star_info.text.strip()
        else:
            star_count_text = 'No specific star count found'

        stars.append(star_count_text)
    
    return repository_links, stars

def fetch_and_save_readme_links(repository_links):
    readme_links = []
    for repo_url in repository_links:
        # Extract the owner and repo name from the URL
        parts = repo_url.split('/')
        owner, repo = parts[-2], parts[-1]
        
        # Construct the URL for the repo's README in the 'main' branch
        readme_main_url = f'https://raw.githubusercontent.com/{owner}/{repo}/main/README.md'
        
        # Check if the README exists in the 'main' branch
        response_main = requests.head(readme_main_url)
        if response_main.status_code == 200:
            readme_links.append(readme_main_url)
        else:
            # Construct the URL for the repo's README in the 'master' branch
            readme_master_url = f'https://raw.githubusercontent.com/{owner}/{repo}/master/README.md'
            
            # Check if the README exists in the 'master' branch
            response_master = requests.head(readme_master_url)
            if response_master.status_code == 200:
                readme_links.append(readme_master_url)
            else:
                print(f"README not found for {repo_url}")
    return readme_links


def summarize_and_classify_readme(readme_link, classes, client, modelname):
    # Read the README file content
    readme_response = requests.get(readme_link)
    readme_text = readme_response.text


    word_list = readme_text.split()  # Splitting the string into a list of words
    number_of_words = len(word_list)

    def keep_first_x_words(s, x):
        words = s.split()  # Splitting the string into a list of words
        first_x_words = words[:x]  # Keeping only the first x words
        return ' '.join(first_x_words)  # Joining the first x words back into a string

    if number_of_words > 5000:
        readme_text = keep_first_x_words(readme_text, 5000)

    print(number_of_words)

    # Summarize the README content
    summary_completion = client.chat.completions.create(
        model=modelname,
        messages=[
            {"role": "system", "content": "You are a helpful assistant. Answer only in English."},
            {"role": "user", "content": f"Summarize this text in 100 words:\n\n{readme_text}"}
        ]
    )
    summary = summary_completion.choices[0].message.content

    # Prepare the classification prompt with the classes from the CSV
    class_prompt = f"Classify this GitHub project based on its Summary. Use only up to 3 words such as {', '.join(classes)} etc. If none of these classes are applicable, return a new class, only return the class nothing else:\n\n{summary}"

    # Classify the GitHub project
    classification_completion = client.chat.completions.create(
        model=modelname,
        messages=[
            {"role": "system", "content": "You are a classifier, return only the class which fits to the text, given to you, do not complain if you can't do it. Answer only in English."},
            {"role": "user", "content": class_prompt}
        ]
    )
    classification = classification_completion.choices[0].message.content
    

    print(classification)

    return summary, classification

def extract_media_links(readme_link):
    """
    Fetches the README file from the given GitHub link and extracts all image, gif, and video links, including those hosted on GitHub or embedded within <video> tags. Prepends the repository link to relative image paths and constructs appropriate links for video IDs or paths.

    Args:
    readme_link (str): The URL to the GitHub README file.

    Returns:
    tuple: A tuple containing two lists, the first list contains image and gif links, and the second list contains video links.
    """
    # Fetch the README content
    response = requests.get(readme_link)
    readme_content = response.text

    # Convert the README link to the base repository URL for prefixing relative links
    base_repo_url = '/'.join(readme_link.split('/')[:-1])

    # Regular expression patterns for extracting image, gif, and video links
    image_pattern = r'(?:!\[.*?\]\((.*?\.(?:png|jpg|jpeg|gif))\)|<img.*?src="([^"]*?\.(?:png|jpg|jpeg|gif))".*?>)'
    github_video_pattern = r'https://github\.com/.+?/blob/.+?/(.+?\.(?:mp4|mov|avi))'
    youtube_video_pattern = r'\b(?:https?://)?(?:www\.)?(?:youtube\.com/watch\?v=|youtu\.be/)([\w\-_]+)\b'
    video_tag_pattern = r'<video.+?src="(.+?)".*?>'
    private_github_video_pattern = r'https://private-user-images\.githubusercontent\.com/.+?/(.+?\.(?:mp4|mov|avi))'

    # Extracting all image and gif links
    raw_media_links = re.findall(image_pattern, readme_content)
    media_links = []

    for link_tuple in raw_media_links:
        # Pick the non-empty path from the tuple
        image_path = link_tuple[1] if link_tuple[1] else link_tuple[0]
        if not image_path.startswith('http'):
            # Ensure the path does not start with a slash to avoid double slashes in the final URL
            if image_path.startswith('/'):
                image_path = image_path[1:]
            full_url = f'{base_repo_url}/{image_path}'
        else:
            full_url = image_path
        media_links.append(full_url)


    # Extracting all video links, including GitHub hosted videos, YouTube URLs, <video> tags, and private GitHub videos
    github_video_links = re.findall(github_video_pattern, readme_content)
    github_video_links = [link if link.startswith('http') else f'{base_repo_url}/{link}' for link in github_video_links]
    youtube_video_ids = re.findall(youtube_video_pattern, readme_content)
    youtube_video_links = [f'https://www.youtube.com/watch?v={video_id}' for video_id in youtube_video_ids]
    video_tag_links = re.findall(video_tag_pattern, readme_content)
    video_tag_links = [link if link.startswith('http') else f'{base_repo_url}/{link}' for link in video_tag_links]
    private_github_video_links = re.findall(private_github_video_pattern, readme_content)
    private_github_video_links = [link if link.startswith('http') else f'{base_repo_url}/{link}' for link in private_github_video_links]

    # Combining all video links into a single list
    video_links = github_video_links + youtube_video_links + video_tag_links + private_github_video_links

    return (media_links, video_links)

def fetch_repository_stars(readme_link):
    """
    Fetches the number of stars for a GitHub repository given a README link.

    Args:
    readme_link (str): The URL to the GitHub README file.

    Returns:
    int: The number of stars the repository has.
    """
    # Extract the GitHub API URL for the repository from the README link
    api_url_pattern = r"https://raw\.githubusercontent\.com/(.*?)/(.*?)/"
    match = re.search(api_url_pattern, readme_link)
    if not match:
        print("Invalid README link provided.")
        return 0

    user, repo = match.groups()
    api_url = f"https://api.github.com/repos/{user}/{repo}"

    # Make a request to the GitHub API to get repository details
    response = requests.get(api_url)
    if response.status_code != 200:
        print(f"Failed to fetch repository details. Status code: {response.status_code}")
        return 0

    # Extract the number of stars from the response
    repo_details = response.json()
    stars = repo_details.get("stargazers_count", 0)

    return stars

def get_column_from_csv(file_name, column_name):
    """
    Extracts a specific column from a CSV file and returns it as a list. If the column is not found,
    or the file does not exist, is empty, or has no data rows, returns an empty list.

    Args:
    file_name (str): The name of the CSV file.
    column_name (str): The name of the column to extract.

    Returns:
    list: A list containing all the values from the specified column, or an empty list in case of errors.
    """

    column_data = []
    # Check if file exists and is not empty
    if not os.path.exists(file_name) or os.path.getsize(file_name) == 0:
        print(f"File {file_name} not found or is empty.")
        return column_data  # Return empty list if file not found or is empty

    try:
        with open(file_name, mode='r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            if column_name not in reader.fieldnames:
                print(f"Column {column_name} not found in the file.")
                return column_data  # Return empty list if column not found
            
            for row in reader:
                column_data.append(row[column_name])
            if not column_data:  # Check if the column was found but no data was added
                print(f"No data found in column {column_name}.")
                return []  # Return empty list if no data found
    except Exception as e:
        print(f"An error occurred: {e}")
        return column_data  # Return empty list in case of other errors

    return column_data

# def is_suitable_for_blogpost(media_link, summary, client):
#     """
#     Checks if the provided media link (image, video, or gif) is suitable as a representation for a blog post about the GitHub repository.
#     It uses the GPT-4 Vision API to analyze the media and ensure it's not a badge or contains unrelated content.

#     Args:
#     media_link (str): The link to the media file (image, video, or gif).
#     summary (str): The summary of the README.md file of the GitHub repository.

#     Returns:
#     bool: True if the media is suitable for the blog post, False otherwise.
#     """

#     # Craft the prompt for the GPT-4 Vision API
#     messages = [
#         {
#             "role": "user",
#             "content": [
#                 {"type": "text", "text": f"Analyze this media to determine if it is suitable for a blog post about a GitHub repository with the following summary: '{summary}'. The media should not be a badge or contain unrelated content. Return 'suitable' if media is suitable and 'not_suitable' if otherwise"},
#                 {"type": "image_url", "image_url": {"url": media_link}},
#             ],
#         }
#     ]

#     # Call the GPT-4 Vision API
#     try:
#         response = client.chat.completions.create(
#             model="gpt-4-vision-preview",
#             messages=messages,
#             max_tokens=300
#         )

#         # Analyze the response to determine suitability
#         decision_text = response.choices[0].message.content
#         print(decision_text)
        
#         if "suitable" in decision_text:
#             return True
#         else:
#             return False
#     except Exception as e:
#         print(f"An error occurred while analyzing the media link: {e}")
#         return False
    
def fetch_repository_creation_date(repo_link):
    """
    Fetches the creation date of a GitHub repository given its link.

    Args:
    repo_link (str): The URL to the GitHub repository.

    Returns:
    str: The creation date of the repository in ISO 8601 format (YYYY-MM-DDTHH:MM:SSZ).
    """
    # Extract the owner and repo name from the URL
    parts = repo_link.split('/')
    owner, repo = parts[-2], parts[-1]

    # Construct the GitHub API URL for fetching repository details
    api_url = f"https://api.github.com/repos/{owner}/{repo}"

    # Send a request to the GitHub API
    response = requests.get(api_url, headers={"Accept": "application/vnd.github.v3+json"})

    if response.status_code == 200:
        repo_data = response.json()
        # Extract the creation date
        creation_date = repo_data['created_at']
        return creation_date
    else:
        print(f"Failed to fetch repository details for {repo_link}. Status code: {response.status_code}")
        return None
    
def create_a_blogpost_readme(readme_link, client, modelname):
    # Read the README file content
    readme_response = requests.get(readme_link)
    readme_text = readme_response.text


    word_list = readme_text.split()  # Splitting the string into a list of words
    number_of_words = len(word_list)

    def keep_first_x_words(s, x):
        words = s.split()  # Splitting the string into a list of words
        first_x_words = words[:x]  # Keeping only the first x words
        return ' '.join(first_x_words)  # Joining the first x words back into a string

    if number_of_words > 4000:
        readme_text = keep_first_x_words(readme_text, 4000)

    # Prepare the classification prompt with the classes from the CSV
    blog_prompt = """
    
    Write a SEO-optimized Title for this blog post. \n\n
    Write a blogpost text, not longer than 5 sentences. \n\n
    Write a SEO-optimized Meta Description for this blog post. \n\n

    Return only a json nothing else, not in ```json ``` tags, the format should be {"Title":"<SEO-optimized Title>", "Blogpost":"<blogpost>", "Meta_Description":"<Meta Description>"}\n\n
    Do not return not in ```json ``` tags.\n\n
    
    For this text:\n\n

    """ + str(readme_text)

    # Classify the GitHub project
    blog_completion = client.chat.completions.create(
        model=modelname,
        messages=[
            {"role": "system", "content": "You are a helpful assistant. Answer only in English."},
            {"role": "user", "content": blog_prompt}
        ]
    )
    blog_text = blog_completion.choices[0].message.content

    print(blog_text)

    return blog_text

def get_stars_count(repo_url, period='week'):
    """
    Get the number of stars added to a GitHub repository within the last week or day.
    
    Parameters:
    - repo_url: str, the full URL of the GitHub repository.
    - period: str, either 'week' or 'day' to specify the period for counting stars.
    
    Returns:
    - int, the number of stars added in the specified period.
    """
    # Extract the owner and repo name from the URL
    parts = repo_url.split('/')
    owner, repo = parts[-2], parts[-1]
    
    # GitHub API endpoint for stargazers
    api_url = f'https://api.github.com/repos/{owner}/{repo}/stargazers'
    
    # Prepare headers to request detailed stargazers information with timestamps
    headers = {
        'Accept': 'application/vnd.github.v3.star+json'
    }
    
    # Calculate the start time for counting stars
    if period == 'week':
        start_time = datetime.now() - timedelta(weeks=1)
    elif period == 'day':
        start_time = datetime.now() - timedelta(days=1)
    else:
        raise ValueError("Period must be 'week' or 'day'")
    
    # Make the request to GitHub API
    response = requests.get(api_url, headers=headers)
    response.raise_for_status()  # Ensure we got a successful response
    
    # Filter stars by the specified period
    stars = [star for star in response.json() if datetime.strptime(star['starred_at'], '%Y-%m-%dT%H:%M:%SZ') > start_time]
    
    return len(stars)

def remove_json_tags(s):
    # Removing the starting tag
    if s.startswith("```json "):
        s = s.replace("```json ", "", 1)
    
    # Removing the ending tag
    if s.endswith("```"):
        s = s.rsplit("```", 1)[0]
    
    return s


def process_trending_repositories_and_create_csv(openai_api_key=None, 
                                                 CSV_PATH = './trending_repositories_summary.csv', 
                                                 ClassName = 'Classification',
                                                 url = 'https://github.com/trending/python?since=daylie',
                                                 local_model = False,
                                                 modelname = 'gpt-3.5-turbo' 
                                                 ):

    if not openai_api_key:
        from dotenv import load_dotenv
        load_dotenv()
        openai_api_key = os.getenv("OPENAI_API_KEY")

    if local_model:
        client = openai.OpenAI(api_key=openai_api_key, base_url="http://localhost:11434/v1")
    else: 
        client = openai.OpenAI(api_key=openai_api_key)

    # Fetch trending repositories
    repository_links, stars = fetch_trending_repositories(url)
    # Fetch and save READMEs
    readmes = fetch_and_save_readme_links(repository_links)

    existing_links = []
    # Check if CSV file exists, if not, create it and write the header
    if not os.path.exists(CSV_PATH):
        with open(CSV_PATH, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(['Date', 
                             'Repository-Link', 
                             'Github-Link', 
                             'Summary', 
                             'Blog-Title', 
                             'Blog-Post',
                             'Meta-Description',
                             ClassName, 
                             'Star-Count-Delta', 
                             'Image-Links', 
                             'Video-Links', 
                             'Stars', 
                             'Repository-Creation-Date'])  # Added 'Repository-Creation-Date' column
    else:
        # If file exists, read existing GitHub links to avoid duplicates
        with open(CSV_PATH, mode='r', newline='', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            existing_links = [row['Github-Link'] for row in reader]


    classes = list(set(get_column_from_csv(CSV_PATH, ClassName)))+["Artificial Intelligence", "Machine Learning", "Language Models", "Deep Learning", "Computer Vision", "Data Science"]
    print(classes)

    # Append data to CSV file
    with open(CSV_PATH, mode='a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)

        for index, (readme_link, repository_link, star_count_delta) in enumerate(zip(readmes, repository_links, stars)):
            if readme_link not in existing_links:  # Skip links that are already in the CSV
                summary, classification = summarize_and_classify_readme(readme_link, classes=classes, client=client, modelname=modelname)

                blog_text_json = create_a_blogpost_readme(readme_link, client=client, modelname=modelname)
                print(star_count_delta)

                try:
                    blog_text_data = remove_json_tags(blog_text_json)
                    blog_text_data = json.loads(blog_text_json)
                    print(blog_text_data)
                    blog_title = blog_text_data.get("Title", "")
                    print(blog_title)
                    blog_post = blog_text_data.get("Blogpost", "")
                    meta_description = blog_text_data.get("Meta_Description", "")
                except json.JSONDecodeError:
                    blog_title = ""
                    blog_post = ""
                    meta_description = ""

                classes.append(classification)
                classes = list(set(classes))
                print(classes)
                image_links, video_links = extract_media_links(readme_link)

                stars = fetch_repository_stars(readme_link)  # Assuming this function exists and fetches the number of stars for a repository
                creation_date = fetch_repository_creation_date(repository_link)  # Fetching repository creation date
                writer.writerow([datetime.now().strftime('%Y-%m-%d'), repository_links[index], 
                                 readme_link, 
                                 summary, 
                                 blog_title, 
                                 blog_post, 
                                 meta_description, 
                                 classification, 
                                 star_count_delta,
                                 '; '.join(image_links), 
                                 '; '.join(video_links), 
                                 stars, 
                                 creation_date])  # Added creation_date to the row


class Main:
    def __init__(self, openai_api_key=None, CSV_PATH='./trending_repositories_summary.csv', ClassName='Classification', url='https://github.com/trending/python?since=weekly', local_model=False, modelname=None):
        self.openai_api_key = openai_api_key
        self.CSV_PATH = CSV_PATH
        self.ClassName = ClassName
        self.url = url
        self.local_model = local_model
        self.modelname = modelname

    def run(self):
        process_trending_repositories_and_create_csv(self.openai_api_key, self.CSV_PATH, self.ClassName, self.url, self.local_model, self.modelname)

    
            
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--openai_api_key', type=str, default=None)
    parser.add_argument('--CSV_PATH', type=str, default='./trending_repositories_summary.csv')
    parser.add_argument('--ClassName', type=str, default='Classification')
    parser.add_argument('--url', type=str, default='https://github.com/trending/python?since=weekly')
    parser.add_argument('--local_model', type=bool, default=False)
    parser.add_argument('--modelname', type=str, default="gpt-3.5-turbo-0125")
    args = parser.parse_args()

    main_instance = Main(args.openai_api_key, args.CSV_PATH, args.ClassName, args.url, args.local_model, args.modelname)
    main_instance.run()
