import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

api_key = os.getenv('OPENAI_API_KEY')
base_url = os.getenv('OPENAI_API_BASE')

print(f"debug base_url: {base_url}, api_key: {api_key[0:10]}******")

client = OpenAI(api_key=api_key, base_url=base_url)

def query(user_prompt):
    """
    发送用户提示到 OpenAI API 并返回响应内容
    
    参数:
        user_prompt (str): 用户输入的提示内容
        
    返回:
        str: AI 的响应内容
    """
    
    try:
        response = client.chat.completions.create(
            model="o3-mini",
            messages=[
                {"role": "user", "content": user_prompt}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"错误: {str(e)}"

if __name__ == "__main__":
    while True:
        user_prompt = input("请输入您的问题: ")
        if user_prompt.lower() == "exit":
            exit()
        print(query(user_prompt))