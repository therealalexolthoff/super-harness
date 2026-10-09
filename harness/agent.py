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
    """ Run the agent's conversation loop """
    # The conversation history. This is the entire memory of the agent. 
    # Every turn, we append to it and send the whole thing to the model.
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    print("Agent ready. Type 'quit' or 'exit' to leave. \n")

    while True:
        # 1. Get user input
        user_input = input("you > ").strip()

        # 2. Allow the user to leave cleanly
        if user_input in {"quit", "exit"}:
            print("Goodbye!")
            break
        #Skip empty lines without making a model call
        elif not user_input:
            continue

        # 3. Append the user's message to the history
        messages.append({"role":"user", "content": user_input})

        # 4. Call the model with the full conversation so far.
        response = client.chat. completions.create(
            model=MODEL,
            messages=messages,
            extra_body = EXTRA_BODY,
            tools = registry.get_schemas()
        )
        message = response.choices[0].message
        # If the model asks for a tool call, handle it before producing the user-facing reply. Minimum-viable dispatch: one round only.
        if message.tool_calls:
            # Step 1: record the model's tool-call message in history so the upcoming tool-result messages have something to reference.
            messages.append(message)
            # Step 2: Run each requested tool and append its result to history using the matching tool_call_id so the model can pair them up.

            for call in message.tool_calls:
                arguments = json.loads(call.function.arguments)
                result = registry.dispatch(call.function.name, arguments)
                messages.append({
                    "role": "tool",
                    "tool_call_id": call.id,
                    "content": result,
                })
            # Step 3: re-call the model now that the tool results are in context. This second call produces the model's final text reply.
            response = client.chat.completions.create(
                model=MODEL,
                messages=messages,
                tools=registry.get_schemas()
                )
            message = response.choices[0].message
    #  Either from the first call (no tools needed) or the second (after dispatch).
        assistant_text = message.content
        messages.append({"role": "assistant", "content": assistant_text})
        print(f"\n agent > {assistant_text}\n")
    
if __name__ == "__main__":
    run()
