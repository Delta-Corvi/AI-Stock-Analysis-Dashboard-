import os
from dotenv import load_dotenv
import logging
from data.data_provider import YFinanceDataProvider
from gemini_summarizer import summarize_with_gemini

logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class FinanceAgent:
    def __init__(self):
        # Try to get the API key from the environment
        self.api_key = os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY')

        if not self.api_key:
            logger.error("GEMINI_API_KEY not found in environment variables.")
            # Don't raise an error immediately, allows the app to start
            logger.warning("App will start but Gemini functionality may be limited")

        self.data_provider = YFinanceDataProvider()

    def run(self, query: str, ticker: str):
        try:
            # Check if the API key is available
            if not self.api_key:
                return "Error: Gemini API key not configured. Please set GEMINI_API_KEY environment variable."

            stock_data = self.data_provider.get_stock_data(ticker)
            if not stock_data:
                return "Error: Could not retrieve stock data."

            #Combine data and user query for summarization


            text_to_summarize = f"{query}. Stock data: {stock_data}"
            summary = summarize_with_gemini(text_to_summarize, self.api_key)

            return summary
        except Exception as e:
            logger.error(f"Error running Finance Agent: {e}")
            return f"Error: Could not retrieve financial summary. {str(e)}"