import openai


openai.api_base = "http://localhost:4891/v1"
#openai.api_base = "https://api.openai.com/v1"

openai.api_key = "not needed for a local LLM"

client = openai.OpenAI()

# # Set up the prompt and other parameters for the API request
# prompt = "Who is Michael Jordan?"

# # model = "gpt-3.5-turbo"
# #model = "mpt-7b-chat"
# model = "gpt4all-j-v1.3-groovy"

# # Make the API request
# response = openai.Completion.create(
#     model=model,
#     prompt=prompt,
#     max_tokens=50,
#     temperature=0.28,
#     top_p=0.95,
#     n=1,
#     echo=True,
#     stream=False
# )

# # Print the generated completion
# print(response)


blog_prompt = """

Write a SEO-optimized Title for this blog post. \n\n
Write a blogpost text, not longer than 5 sentences. \n\n
Write a SEO-optimized Meta Description for this blog post. \n\n

Return only a json nothing else, not in ```json ``` tags, the format should be {"Title":"<SEO-optimized Title>", "Blogpost":"<blogpost>", "Meta_Description":"<Meta Description>"}\n\n


For this text:\n\n

"""

# Classify the GitHub project
blog_completion = client.chat.completions.create(
    model="gpt-3.5-turbo-0125",
    messages=[
        {"role": "system", "content": "You are a helpful assistant. Answer only in English."},
        {"role": "user", "content": blog_prompt}
    ]
)
blog_text = blog_completion.choices[0].message.content

print(blog_text)