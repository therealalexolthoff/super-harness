from openai import OpenAI

load_dotenv()

client = OpenAI()
response = client.chat.completions.create(
    model="gpt-4o-mini",
    message=[("role": "user", "content": "Say 'setup works' and nothng else.")]
)

print(response.choices[0].message.content)