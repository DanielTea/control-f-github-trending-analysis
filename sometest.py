import requests
from bs4 import BeautifulSoup

def fetch_trending_repositories(url='https://github.com/trending/python?since=daily'):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    repo_elements = soup.find_all('article', class_='Box-row')

    repositories_info = []
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

        repositories_info.append({
            'url': repo_url,
            'stars_this_period': star_count_text
        })

    return repositories_info

# Example usage
url = 'https://github.com/trending/python?since=weekly'  # Adjust the URL for weekly or daily trends as needed
trending_repositories = fetch_trending_repositories(url)
for repo in trending_repositories:
    print(repo['url'], repo['stars_this_period'])
