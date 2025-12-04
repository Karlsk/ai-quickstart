import os
from pydoc import cli
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv('OPENAI_API_KEY')
base_url = os.getenv('OPENAI_API_BASE')
print(f"-- debug -- openai base url is {base_url} api key is {api_key[0:10]}******")
if base_url is None or api_key is None:
    print("Please set the OPENAI_API_BASE and OPENAI_API_KEY environment variables.")
    exit(1)

client = OpenAI(api_key=api_key, base_url=base_url)

response = client.chat.completions.create(
    model="o3-mini",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Hello world!"},
    ],
)

print(response.choices[0].message.content)
