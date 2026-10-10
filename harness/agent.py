import os
from dotenv import load_dotenv
from openai import OpenAI
import json
from harness.system_prompt import SYSTEM_PROMPT
from harness.tools.registry import registry


load_dotenv()

# Decide what backend to use based on which key is set in .env.
# This is a configuration-time choice - change .env, not code

if os.getenv("KIMI_API_KEY"):
    MODEL = "kimi-k2.6"
    client = OpenAI(
        api_key=os.getenv("KIMI_API_KEY"),
        base_url=os.getenv("KIMI_BASE_URL")
    )
# K2.6 supports thinking and non-thinking modes. We disable think to keep response shape identical to OpenAI - no reasoning_content to handle, no preservation requirements in multi-turn dispatch.
    EXTRA_BODY = {"thinking": {"type": "disabled"}}
else: 
    MODEL='gpt-4o-mini'
    client = OpenAI()
    EXTRA_BODY = {}

def run():
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    print("Agent ready. Type 'quit' or 'exit' to leave.\n")

    while True:
        user_input = input("you > ").strip()
        if user_input in {"quit", "exit"}:
            print("Goodbye!")
            break
        if not user_input:
            continue

        messages.append({"role": "user", "content": user_input})

        # Keep calling the model until it replies without tool calls
        while True:
            response = client.chat.completions.create(
                model=MODEL,
                messages=messages,
                extra_body=EXTRA_BODY,
                tools=registry.get_schemas(),
            )
            message = response.choices[0].message
            messages.append(message)  # keeps tool_calls intact

            if not message.tool_calls:
                break

            for call in message.tool_calls:
                try:
                    arguments = json.loads(call.function.arguments)
                    result = registry.dispatch(call.function.name, arguments)
                except Exception as e:
                    result = f"Error: {e}"
                messages.append({
                    "role": "tool",
                    "tool_call_id": call.id,
                    "content": str(result),
                })

        print(f"\nagent > {message.content}\n")
    
if __name__ == "__main__":
    run()
