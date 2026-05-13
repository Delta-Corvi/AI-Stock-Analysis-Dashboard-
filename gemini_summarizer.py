from google import genai
from google.genai import types
from dotenv import load_dotenv
import os

load_dotenv()

def summarize_with_gemini(text: str, api_key: str):
    """Summarizes a text using Gemini."""
    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model='gemini-1.5-flash',
            contents=f"Summarize the following text: {text}",
        )
        return response.text
    except Exception as e:
        print(f"Error during summarization with Gemini: {e}")
        return "Error: Could not generate summary with Gemini."
