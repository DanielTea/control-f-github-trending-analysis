import requests
from bs4 import BeautifulSoup
import os
from openai import OpenAI
import csv
from datetime import datetime
import re
    # if not classes:
    #     classes = ["Artificial Intelligence", "Network Infrastructure"]

def fetch_trending_repositories():
    # URL of the trending Python repositories on GitHub
    url = 'https://github.com/trending/python?since=daily'

    # Send a request to the URL
    response = requests.get(url)

    # Parse the HTML content of the page
    soup = BeautifulSoup(response.text, 'html.parser')

    # Find all elements containing repository links, adjusting for the provided structure
    repo_elements = soup.find_all('h2', class_='h3 lh-condensed')

    repository_links = []
    # Extract and print the URLs of the repositories
    for repo_element in repo_elements:
        a_tag = repo_element.find('a')
        repo_url = 'https://github.com' + a_tag['href']
        print(repo_url)
        repository_links.append(repo_url)
    
    return repository_links

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


def summarize_and_classify_readme(readme_link, classes, client):
    # Read the README file content
    readme_response = requests.get(readme_link)
    readme_text = readme_response.text

    # Summarize the README content
    summary_completion = client.chat.completions.create(
        model="gpt-4-0125-preview",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": f"Summarize this text in 100 words:\n\n{readme_text}"}
        ]
    )
    summary = summary_completion.choices[0].message.content

    # Prepare the classification prompt with the classes from the CSV
    class_prompt = f"Classify this GitHub project based on its README. Use only one or two words such as {', '.join(classes)} etc. If none of these classes are applicable, return a new class, only return the class nothing else:\n\n{readme_text}"

    # Classify the GitHub project
    classification_completion = client.chat.completions.create(
        model="gpt-4-0125-preview",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
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
    image_pattern = r'!\[.*?\]\((.*?\.(?:png|jpg|jpeg|gif))\)'
    github_video_pattern = r'https://github\.com/.+?/blob/.+?/(.+?\.(?:mp4|mov|avi))'
    youtube_video_pattern = r'\b(?:https?://)?(?:www\.)?(?:youtube\.com/watch\?v=|youtu\.be/)([\w\-_]+)\b'
    video_tag_pattern = r'<video.+?src="(.+?)".*?>'

    # Extracting all image and gif links
    raw_media_links = re.findall(image_pattern, readme_content)
    media_links = [link if link.startswith('http') else f'{base_repo_url}/{link}' for link in raw_media_links]

    # Extracting all video links, including GitHub hosted videos, YouTube URLs, and <video> tags
    github_video_links = re.findall(github_video_pattern, readme_content)
    github_video_links = [link if link.startswith('http') else f'{base_repo_url}/{link}' for link in github_video_links]
    youtube_video_ids = re.findall(youtube_video_pattern, readme_content)
    youtube_video_links = [f'https://www.youtube.com/watch?v={video_id}' for video_id in youtube_video_ids]
    video_tag_links = re.findall(video_tag_pattern, readme_content)
    video_tag_links = [link if link.startswith('http') else f'{base_repo_url}/{link}' for link in video_tag_links]

    # Combining all video links into a single list
    video_links = github_video_links + youtube_video_links + video_tag_links

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

def is_suitable_for_blogpost(media_link, summary, client):
    """
    Checks if the provided media link (image, video, or gif) is suitable as a representation for a blog post about the GitHub repository.
    It uses the GPT-4 Vision API to analyze the media and ensure it's not a badge or contains unrelated content.

    Args:
    media_link (str): The link to the media file (image, video, or gif).
    summary (str): The summary of the README.md file of the GitHub repository.

    Returns:
    bool: True if the media is suitable for the blog post, False otherwise.
    """

    # Craft the prompt for the GPT-4 Vision API
    messages = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": f"Analyze this media to determine if it is suitable for a blog post about a GitHub repository with the following summary: '{summary}'. The media should not be a badge or contain unrelated content. Return 'suitable' if media is suitable and 'not_suitable' if otherwise"},
                {"type": "image_url", "image_url": {"url": media_link}},
            ],
        }
    ]

    # Call the GPT-4 Vision API
    try:
        response = client.chat.completions.create(
            model="gpt-4-vision-preview",
            messages=messages,
            max_tokens=300
        )

        # Analyze the response to determine suitability
        decision_text = response.choices[0].message.content
        print(decision_text)
        
        if "suitable" in decision_text:
            return True
        else:
            return False
    except Exception as e:
        print(f"An error occurred while analyzing the media link: {e}")
        return False
    
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


def process_trending_repositories_and_create_csv():

    from dotenv import load_dotenv
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    client = OpenAI(api_key=api_key)

    # Fetch trending repositories
    repository_links = fetch_trending_repositories()

    # Fetch and save READMEs
    readmes = fetch_and_save_readme_links(repository_links)
    CSV_PATH = './trending_repositories_summary.csv'
    ClassName = 'Classification'

    existing_links = []
    # Check if CSV file exists, if not, create it and write the header
    if not os.path.exists(CSV_PATH):
        with open(CSV_PATH, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(['Date', 'Repository-Link', 'Github-Link', 'Summary', ClassName, 'Image-Links', 'Video-Links', 'Stars', 'Suitable-Image-Links', 'Suitable-Video-Links', 'Repository-Creation-Date'])  # Added 'Repository-Creation-Date' column
    else:
        # If file exists, read existing GitHub links to avoid duplicates
        with open(CSV_PATH, mode='r', newline='', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            existing_links = [row['Github-Link'] for row in reader]

    classes = list(set(get_column_from_csv(CSV_PATH, ClassName)))
    print(classes)

    # Append data to CSV file
    with open(CSV_PATH, mode='a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)

        for index, (readme_link, repository_link) in enumerate(zip(readmes, repository_links)):
            if readme_link not in existing_links:  # Skip links that are already in the CSV
                summary, classification = summarize_and_classify_readme(readme_link, classes=classes, client=client)
                classes.append(classification)
                classes = list(set(classes))
                print(classes)
                image_links, video_links = extract_media_links(readme_link)
                
                suitable_image_links = []
                for image_link in image_links:
                    if is_suitable_for_blogpost(image_link, summary, client):
                        suitable_image_links.append(image_link)

                suitable_video_links = []
                for video_link in video_links:
                    if is_suitable_for_blogpost(video_link, summary, client):
                        suitable_video_links.append(video_link)

                stars = fetch_repository_stars(readme_link)  # Assuming this function exists and fetches the number of stars for a repository
                creation_date = fetch_repository_creation_date(repository_link)  # Fetching repository creation date
                writer.writerow([datetime.now().strftime('%Y-%m-%d'), repository_links[index], readme_link, summary, classification, '; '.join(image_links), '; '.join(video_links), stars, '; '.join(suitable_image_links), '; '.join(suitable_video_links), creation_date])  # Added creation_date to the row

process_trending_repositories_and_create_csv()