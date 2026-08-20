from openai import OpenAI

client = OpenAI(
    base_url="http://111.37.195.37:8000/v1",
    api_key="dummy"
)

res = client.chat.completions.create(
    model="Qwen3-14B",
    messages=[{"role":"user","content":"你好"}]
)
print(res.choices[0].message.content)