import gradio as gr
from agents.finance_agent import FinanceAgent
from agents.analysis_agent import AnalysisAgent
import os
import logging

logger = logging.getLogger(__name__)

class GradioInterface:
    def __init__(self):
        self.finance_agent = FinanceAgent()
        self.analysis_agent = AnalysisAgent()

    def analyze_stock(self, ticker: str, report_type: str, period: str = "1y", include_forecast: bool = True):
        """
        Enhanced stock analysis with forecasting capabilities
        """
        try:
            # Get financial summary
            finance_summary = self.finance_agent.run(report_type.replace("ticker", ticker), ticker=ticker)

            # Get enhanced charts with forecasting
            candlestick_chart, technical_indicators_chart = self.analysis_agent.get_stock_charts(
                ticker, period, include_forecast=include_forecast
            )

            # Get forecast summary if forecasting is enabled
            forecast_summary = ""
            if include_forecast:
                forecast_summary = self.analysis_agent.get_forecast_summary(ticker, period)

            return finance_summary, candlestick_chart, technical_indicators_chart, forecast_summary

        except Exception as e:
            logger.error(f"Error analyzing stock: {e}")
            return "Error: Could not analyze stock.", None, None, "Forecast unavailable due to error."

    def create_interface(self):
        # Define the mapping between display names and actual report types
        report_type_mapping = {
            "📊 Detailed Financial Report": "Give a comprehensive financial analysis report about ticker stock including key metrics, ratios, and market position.",
            "💰 Dividend Analysis": "Provide detailed dividend information and yield analysis for ticker stock.",
            "📈 Technical Analysis": "Perform technical analysis on ticker stock including trend analysis and key indicators.",
            "🔍 Risk Assessment": "Analyze the risk profile and volatility characteristics of ticker stock."
        }

        # Custom CSS for better styling
        custom_css = """
        .gradio-container {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        }
        .panel {
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            border-radius: 10px;
            border: 1px solid rgba(255, 255, 255, 0.2);
        }
        .forecast-panel {
            background: linear-gradient(135deg, #fa289d 0%, #57f563 100%);
            color: white;
            padding: 20px;
            border-radius: 10px;
            margin: 10px 0;
        }

        """

        with gr.Blocks(css=custom_css, title="🚀 AI Stock Analysis Dashboard") as demo:
            # Header
            gr.HTML("""
            <div style="text-align: center; padding: 20px; background: rgba(0,0,0,0.1); border-radius: 10px; margin-bottom: 20px;">
                <h1 style="color: white; font-size: 2.5em; margin: 0;">
                    🚀 AI Stock Analysis Dashboard
                </h1>
                <p style="color: rgba(255,255,255,0.8); font-size: 1.2em; margin: 10px 0 0 0;">
                    Advanced Technical Analysis with AI-Powered Forecasting
                </p>
            </div>
            """)

            with gr.Row():
                with gr.Column(scale=1):
                    with gr.Group():
                        gr.Markdown("### 📋 Analysis Settings")

                        ticker_input = gr.Textbox(
                            label="🎯 Stock Ticker Symbol",
                            placeholder="e.g., AAPL, MSFT, TSLA",
                            value="AAPL"
                        )

                        period_input = gr.Dropdown(
                            choices=["1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max"],
                            label="📅 Historical Data Period",
                            value="1y"
                        )

                        report_type_input = gr.Radio(
                            choices=list(report_type_mapping.keys()),
                            label="📊 Analysis Type",
                            value=list(report_type_mapping.keys())[0]
                        )

                        include_forecast_input = gr.Checkbox(
                            label="🔮 Include 15-Day Price Forecast",
                            value=True
                        )

                        analyze_button = gr.Button(
                            "🚀 Run Analysis",
                            variant="primary",
                            size="lg"
                        )
            # Examples section

            gr.Markdown("💡 Try These Examples")
            gr.Examples(
                examples=[
                    ["AAPL", "1y", "📊 Detailed Financial Report", True],
                    ["MSFT", "6mo", "📈 Technical Analysis", True],
                    ["TSLA", "3mo", "🔍 Risk Assessment", True],
                    ["GOOGL", "1y", "💰 Dividend Analysis", False],
                    ["NVDA", "2y", "📊 Detailed Financial Report", True],
                ],
                inputs=[ticker_input, period_input, report_type_input, include_forecast_input],
                label=""
            )
            # Results Section
            with gr.Row():
                with gr.Column():
                    with gr.Tab("📈 Price Charts"):
                        candlestick_chart_output = gr.Plot(
                            label="Enhanced Candlestick Chart with Trend Lines & Forecasts"
                        )

                    with gr.Tab("📊 Technical Indicators"):
                        technical_indicators_chart_output = gr.Plot(
                            label="Advanced Technical Indicators"
                        )

                with gr.Column():
                    with gr.Tab("🤖 AI Analysis"):
                        finance_summary_output = gr.Markdown(
                            label="AI-Generated Financial Analysis"
                        )

                    with gr.Tab("🔮 Forecast Summary"):
                        forecast_summary_output = gr.Markdown(
                            label="15-Day Price Forecast Summary",
                            elem_classes=["forecast-panel"]
                        )


            # Event handler
            analyze_button.click(
                fn=lambda ticker, selected_report_name, period, include_forecast: self.analyze_stock(
                    ticker, report_type_mapping[selected_report_name], period, include_forecast
                ),
                inputs=[ticker_input, report_type_input, period_input, include_forecast_input],
                outputs=[finance_summary_output, candlestick_chart_output, technical_indicators_chart_output, forecast_summary_output]
            )

            # Footer
            gr.HTML("""
            <div style="text-align: center; padding: 20px; margin-top: 30px; background: rgba(0,0,0,0.1); border-radius: 10px;">
                <p style="color: rgba(255,255,255,0.6); margin: 0;">
                    ⚠️ <strong>Disclaimer:</strong> This analysis is for educational purposes only.
                    Not financial advice. Past performance does not guarantee future results.
                </p>
            </div>
            """)

        return demo

if __name__ == '__main__':
    interface = GradioInterface()
    demo = interface.create_interface()
    demo.launch(show_error=True)