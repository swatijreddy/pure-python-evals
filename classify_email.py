import time
from anthropic import Anthropic
from anthropic import APIConnectionError, RateLimitError, AuthenticationError
from dotenv import load_dotenv

load_dotenv()

# Connects to Claude's API using your key from .env

client = Anthropic()
MODEL = "claude-haiku-4-5-20251001"

# Fixed categories Claude is allowed to choose from

LABELS = [
    "Bills & Utilities",
    "Job Alerts",
    "Shipping & Orders",
    "Learning & Courses",
    "High Priority",
    "Alerts & Newsletters"
]


# SYSTEM UNDER TEST — sends one email to Claude, returns its predicted label

def classify_email(email_text):
    categories = ",".join(LABELS)
    prompt = f"""Classify this email exactly into one of these email categories:{categories}.\n
  Reply with ONLY the category name, nothing else\n
  Email:
  {email_text}"""

    # OPERATIONAL CHECK — measure how long the API call takes

    start_time = time.time()

    # ERROR HANDLING — catches connection/rate-limit/auth failures instead of crashing

    try:

        message = client.messages.create(
            model=MODEL,
            max_tokens=50,
            temperature=0,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )
        end_time = time.time()
        latency = end_time - start_time
        print(f"Latency:{latency:.2f} seconds")
        return message.content[0].text.strip()

    except APIConnectionError:
        print("Error: couldn't reach Claude API. Check your internet connection")
        return None
    except RateLimitError:
        print("Error: Too many requests")
        return None
    except AuthenticationError:
        print("Error: Unauthorized user or invalid API key")
        return None
