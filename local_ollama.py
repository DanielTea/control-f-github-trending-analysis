import openai

client = openai.OpenAI(api_key="dummy", base_url="http://localhost:11434/v1")

blog_prompt = "Why is the sky blue?"
 # Classify the GitHub project
blog_completion = client.chat.completions.create(
    model="llama2",
    messages=[
        {"role": "system", "content": "You are a helpful assistant. Answer only in English."},
        {"role": "user", "content": blog_prompt}
    ]
)
blog_text = blog_completion.choices[0].message.content

print(blog_text)
#/////////////////////
# import requests
# import re

# # readme_link = "https://raw.githubusercontent.com/maszhongming/Multi-LoRA-Composition/main/README.md"
# readme_link = "https://raw.githubusercontent.com/microsoft/Mastering-GitHub-Copilot-for-Paired-Programming/main/README.md"
#   # Fetch the README content
# response = requests.get(readme_link)
# readme_content = response.text

# # Convert the README link to the base repository URL for prefixing relative links
# base_repo_url = '/'.join(readme_link.split('/')[:-1])

# # Regular expression patterns for extracting image, gif, and video links
# image_pattern = r'(?:!\[.*?\]\((.*?\.(?:png|jpg|jpeg|gif))\)|<img.*?src="([^"]*?\.(?:png|jpg|jpeg|gif))".*?>)'
# github_video_pattern = r'https://github\.com/.+?/blob/.+?/(.+?\.(?:mp4|mov|avi))'
# youtube_video_pattern = r'\b(?:https?://)?(?:www\.)?(?:youtube\.com/watch\?v=|youtu\.be/)([\w\-_]+)\b'
# video_tag_pattern = r'<video.+?src="(.+?)".*?>'
# private_github_video_pattern = r'https://private-user-images\.githubusercontent\.com/.+?/(.+?\.(?:mp4|mov|avi))'

# # Extracting all image and gif links
# raw_media_links = re.findall(image_pattern, readme_content)
# print(raw_media_links)

# # Processed list of media links
# media_links = []

# for link_tuple in raw_media_links:
#     # Pick the non-empty path from the tuple
#     image_path = link_tuple[1] if link_tuple[1] else link_tuple[0]
#     if not image_path.startswith('http'):
#         # Ensure the path does not start with a slash to avoid double slashes in the final URL
#         if image_path.startswith('/'):
#             image_path = image_path[1:]
#         full_url = f'{base_repo_url}/{image_path}'
#     else:
#         full_url = image_path
#     media_links.append(full_url)

# print(media_links)

# # media_links = [link[0] if link[0].startswith('http') else f'{base_repo_url}/{link[0]}' for link in raw_media_links]

# # print(media_links)