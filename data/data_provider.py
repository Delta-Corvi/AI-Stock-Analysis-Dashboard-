import yfinance as yf
import logging
import functools
import datetime
import os
import json

logger = logging.getLogger(__name__)

# Cache configuration
CACHE_DIR = "cache"
os.makedirs(CACHE_DIR, exist_ok=True)  # Create cache directory if it doesn't exist

class YFinanceDataProvider:
    def __init__(self):
        pass

    def _cache_key(self, ticker: str, period: str):
        """Generate a unique cache key based on parameters."""
        return f"{ticker}_{period}.json"

    def _load_from_cache(self, key: str):
        """Load data from cache if present and valid."""
        cache_path = os.path.join(CACHE_DIR, key)
        try:
            if os.path.exists(cache_path):
                # Check if cache has expired (e.g., 24 hours)
                file_creation_time = datetime.datetime.fromtimestamp(os.path.getctime(cache_path))
                if datetime.datetime.now() - file_creation_time < datetime.timedelta(hours=24):
                    with open(cache_path, 'r') as f:
                        return json.load(f)
                else:
                    logger.info(f"Cache expired for {key}, refreshing data.")
                    return None
            else:
                return None
        except Exception as e:
            logger.error(f"Error loading from cache {key}: {e}")
            return None

    def _save_to_cache(self, key: str, data):
        """Save data to cache."""
        cache_path = os.path.join(CACHE_DIR, key)
        try:
            with open(cache_path, 'w') as f:
                json.dump(data, f)
            logger.info(f"Data saved to cache: {key}")
        except Exception as e:
            logger.error(f"Error saving to cache {key}: {e}")

    def get_stock_data(self, ticker: str, period: str = "1y"):
        """Retrieve data from YFinance, using cache if possible."""
        cache_key = self._cache_key(ticker, period)
        cached_data = self._load_from_cache(cache_key)

        if cached_data:
            return cached_data

        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            history = stock.history(period=period)

            data = {
                'current_price': info.get('currentPrice'),
                'market_cap': info.get('marketCap'),
                'fiftyTwoWeekHigh': info.get('fiftyTwoWeekHigh'),
                'fiftyTwoWeekLow': info.get('fiftyTwoWeekLow'),
                'history': history.to_json(date_format='iso') # Convert to JSON
            }

            self._save_to_cache(cache_key, data)
            return data
        except Exception as e:
            logger.error(f"Error fetching data for {ticker}: {e}")
            return None