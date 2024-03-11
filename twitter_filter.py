import csv
import requests
from datetime import datetime, timedelta

def fetch_and_filter_csv(url):
    response = requests.get(url)
    response.raise_for_status()  # Raise an error for bad responses
    
    lines = response.text.splitlines()
    reader = csv.DictReader(lines)
    
    classifications = ["Self-Supervised Learning","Artificial Intelligence", 
                       "Natural Language Processing", "Machine Learning", 
                       "Language Models", "Deep Learning", "Computer Vision", 
                       "Data Science", "AI", "Image Generation Algorithm", 
                       "Computer Vision Platform"]
    
    filtered_data = [
        item for item in reader
        if any(classification in item['Classification'] for classification in classifications)
        and item['Repository-Creation-Date']
        and item['Blog-Title'] is not None
        and item.get('Video-Links') or item.get('Image-Links')
        and is_within_one_month(item['Repository-Creation-Date'])
    ]
    
    # Sort by Date descending
    filtered_data.sort(key=lambda x: datetime.strptime(x['Date'], '%Y-%m-%d'), reverse=True)
    
    # Write to CSV
    with open('./filtered_repositories_summary.csv', 'a', newline='') as file:
        fieldnames = ['Blog-Title', 'Repository-Link', 'Video-Links', 'Image-Links', 'Classification', 'Tweet-Send']
        writer = csv.DictWriter(file, fieldnames=fieldnames)

        if file.tell() == 0:  # Check if file is empty
            writer.writeheader()

        existing_repository_links = set()  # Set to store existing repository links

        # Read existing repository links from the file
        with open('./filtered_repositories_summary.csv', 'r', newline='') as read_file:
            reader = csv.DictReader(read_file)
            for row in reader:
                existing_repository_links.add(row['Repository-Link'])

        for item in filtered_data:
            if item['Repository-Link'] in existing_repository_links:
                continue  # Skip if repository link already exists in the file

            # media_links = item.get('Video-Links', '') + ';' + item.get('Image-Links', '')
            writer.writerow({
                'Blog-Title': item['Blog-Title'],
                'Repository-Link': item['Repository-Link'],
                'Video-Links': item.get('Video-Links', ''),
                'Image-Links': filter_out_badge_images(item.get('Image-Links', '')),
                'Classification': item['Classification'],
                'Tweet-Send': 'False'  # Set Tweet-Send to False for new entry
            })

def is_within_one_month(date_string):

    try:
        format_string = '%Y-%m-%dT%H:%M:%SZ'
        repository_creation_date = datetime.strptime(date_string, format_string)
        one_month_ago = datetime.now() - timedelta(days=30)
        return repository_creation_date > one_month_ago
    except:
        return False

# Start of Selection
def filter_out_badge_images(image_links):
    badgePatterns = ['badge', 'button', 'shield', 'tangram']
    return [link.strip() for link in image_links.split(';') if not any(pattern in link.lower() for pattern in badgePatterns)]
