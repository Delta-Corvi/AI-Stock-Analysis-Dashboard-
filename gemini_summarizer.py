import google.generativeai as genai
from dotenv import load_dotenv
import os

load_dotenv()

def summarize_with_gemini(text: str, api_key: str):
    """Summarizes a text using Gemini."""
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(f"Summarize the following text: {text}")
        return response.text
    except Exception as e:
        print(f"Error during summarization with Gemini: {e}")
        return "Error: Could not generate summary with Gemini."