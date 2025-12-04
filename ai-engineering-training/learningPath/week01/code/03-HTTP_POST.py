import http.client
import json
import os
import ssl
from dotenv import load_dotenv

load_dotenv()

context = ssl._create_unverified_context()
conn = http.client.HTTPSConnection("api.gpt.ge", context=context)
payload = json.dumps({
   "model": "o3-mini",
   "messages": [
      {
         "role": "user",
         "content": "晚上好"
      }
   ],
   "max_tokens": 1688,
   "temperature": 0.5,
   "stream": False
})

# 从环境变量获取API token

api_token = os.getenv('OPENAI_API_KEY')  # 或者使用其他环境变量名

headers = {
   'Content-Type': 'application/json',
   'Authorization': f'Bearer {api_token}'
}
# 打印出请求信息
print(f"-- debug -- request payload is {payload}")
print(f"-- debug -- request headers are {headers}")

conn.request("POST", "/v1/chat/completions", payload, headers)
res = conn.getresponse()
data = res.read()

# 打印原始响应
print("原始响应:")
print(data.decode("utf-8"))

# 解析JSON并提取消息内容
response_json = json.loads(data.decode("utf-8"))
message_content = response_json['choices'][0]['message']['content']
print("\n提取的消息内容:")
print(message_content)