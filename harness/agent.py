import os
from python-dotenv import load_dotenv
from openai import OpenAI

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
    messages = []
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
            extra_body = EXTRA_BODY
        )
        # 5. Extract the assistant's reply
        assistant_message = response.choices[0].message.content

        # 6. Append the assitant's reply to the history.
        messages.append(assistant_message)

        print(f"\n agent > {assistant_message}\n")

if __name__ == "__main__":
    run()
