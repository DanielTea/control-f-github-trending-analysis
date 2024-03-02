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