import os
from dotenv import load_dotenv
from google import genai
from system_prompt import SYSTEM_PROMPT

# Load environment variables from .env file
load_dotenv()

# Configure the Gemini API with the key from .env
api_key = os.getenv("GEMINI_API_KEY")
client = None
if api_key:
    client = genai.Client(api_key=api_key)


def generate_spec(user_prompt: str) -> str:
    """
    Takes a natural language description and returns a structured RPA
    workflow specification using the Gemini API.
    """
    try:
        if not api_key:
            return (
                "Error: GEMINI_API_KEY not found.\n\n"
                "Please copy .env.example to .env and add your API key:\n"
                "  1. Copy .env.example to .env\n"
                "  2. Replace the placeholder with your actual Gemini API key"
            )

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=user_prompt,
            config={"system_instruction": SYSTEM_PROMPT, "temperature": 0.3}
        )
        return response.text

    except Exception as e:
        return f"Error generating spec: {str(e)}"
