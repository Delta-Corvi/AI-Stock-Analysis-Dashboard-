import yfinance as yf
import logging

logger = logging.getLogger(__name__)

class YFinanceDataProvider:
    def __init__(self):
        pass

    def get_stock_data(self, ticker: str):
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            history = stock.history(period="1y")

            data = {
                'current_price': info.get('currentPrice'),
                'market_cap': info.get('marketCap'),
                'fiftyTwoWeekHigh': info.get('fiftyTwoWeekHigh'),
                'fiftyTwoWeekLow': info.get('fiftyTwoWeekLow'),
                'history': history
            }
            return data
        except Exception as e:
            logger.error(f"Error fetching data for {ticker}: {e}")
            return None