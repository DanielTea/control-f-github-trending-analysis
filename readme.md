#GitHub Trending Repositories Analyzer

This Python project is designed to analyze trending Python repositories on GitHub, fetch their READMEs, and perform various operations such as summarization, classification, media link extraction, and more. It leverages requests for HTTP requests, BeautifulSoup for HTML parsing, and OpenAI's GPT models for natural language processing tasks.

##Features

Trending Repositories Fetching: Extracts trending Python repositories from GitHub.
README Fetching and Saving: Retrieves README files for each repository and checks their existence in different branches (main/master).
Summarization and Classification: Summarizes README content and classifies repositories into predefined categories using OpenAI's GPT models.
Media Link Extraction: Extracts image, gif, and video links from README files, differentiating between suitable and unsuitable media for blog posts.
Star Count Retrieval: Fetches the number of stars a repository has received on GitHub.
Repository Creation Date: Determines the creation date of each repository.
CSV Reporting: Compiles and saves the fetched data into a CSV file for further analysis.
