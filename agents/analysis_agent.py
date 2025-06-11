from charting.charts import create_candlestick_chart, create_technical_indicators_chart
from data.data_provider import YFinanceDataProvider
import logging
import pandas as pd
import numpy as np
from io import StringIO  # Added to fix deprecation warning

logger = logging.getLogger(__name__)

class AnalysisAgent:
    def __init__(self):
        self.data_provider = YFinanceDataProvider()

    def _safe_read_json(self, json_data):
        """
        Reads JSON safely to avoid deprecation warning
        """
        try:
            if isinstance(json_data, str):
                # If it's a JSON string, use StringIO
                return pd.read_json(StringIO(json_data))
            elif isinstance(json_data, dict):
                # If it's already a dict, convert directly
                return pd.DataFrame(json_data)
            else:
                # Fallback for other types
                return pd.read_json(json_data)
        except Exception as e:
            logger.error(f"Error reading JSON data: {e}")
            raise

    def get_stock_charts(self, ticker: str, period: str = "1y", include_forecast: bool = True):
        """
        Generate enhanced stock charts with trend lines and forecasts

        Args:
            ticker: Stock symbol
            period: Time period for historical data
            include_forecast: Whether to include price forecasts
        """
        try:
            data = self.data_provider.get_stock_data(ticker, period)
            if not data:
                logger.error(f"No data retrieved for {ticker}")
                return None, None

            # Convert JSON to DataFrame using the safe method
            history = self._safe_read_json(data['history'])

            # Ensure we have enough data
            if len(history) < 30:
                logger.warning(f"Insufficient data for {ticker}, only {len(history)} records")
                include_forecast = False

            # Create enhanced candlestick chart
            candlestick_chart = create_candlestick_chart(history, include_forecast=include_forecast)

            # Create technical indicators chart
            technical_indicators_chart = create_technical_indicators_chart(history)

            return candlestick_chart, technical_indicators_chart

        except Exception as e:
            logger.error(f"Error getting stock charts for {ticker}: {e}")
            return None, None

    def get_forecast_summary(self, ticker: str, period: str = "1y"):
        """
        Generate a text summary of the price forecast
        KEEPS THE 15-DAY FORECAST LOGIC UNCHANGED
        """
        try:
            data = self.data_provider.get_stock_data(ticker, period)
            if not data:
                return "Unable to generate forecast summary - no data available."

            # FIX: Use the safe method to read JSON
            history = self._safe_read_json(data['history'])

            if len(history) < 30:
                return "Insufficient historical data for reliable forecasting."

            # Import the forecast function (UNCHANGED)
            from charting.charts import generate_price_forecast

            # 15-DAY FORECAST LOGIC COMPLETELY UNCHANGED
            forecasts, confidence_intervals = generate_price_forecast(history)

            current_price = history['Close'].iloc[-1]
            forecast_15d = forecasts[-1]

            # Calculate metrics (UNCHANGED)
            expected_return = ((forecast_15d / current_price) - 1) * 100
            volatility_range = confidence_intervals[-1]

            # OUTPUT FORMATTING COMPLETELY UNCHANGED
            summary = f"""
📊 **15-Day Price Forecast Summary for {ticker.upper()}**

🔹 **Current Price**: ${current_price:.2f}
🔹 **15-Day Forecast**: ${forecast_15d:.2f}
🔹 **Expected Return**: {expected_return:+.2f}%

📈 **Confidence Interval (95%)**:
   • Lower Bound: ${volatility_range['lower']:.2f}
   • Upper Bound: ${volatility_range['upper']:.2f}

⚠️ **Risk Assessment**: {"High" if abs(expected_return) > 10 else "Medium" if abs(expected_return) > 5 else "Low"} volatility expected

🎯 **Key Levels to Watch**:
   • Support: ${min(forecasts):.2f}
   • Resistance: ${max(forecasts):.2f}

*Note: This forecast is based on technical analysis and historical patterns. Past performance does not guarantee future results.*
"""

            return summary.strip()

        except Exception as e:
            logger.error(f"Error generating forecast summary: {e}")
            return "Unable to generate forecast summary due to technical error."