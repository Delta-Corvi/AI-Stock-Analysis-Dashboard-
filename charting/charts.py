import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures
from scipy import stats
import datetime

def calculate_trend_lines(history: pd.DataFrame, lookback_period=50):
    """Calculate support and resistance trend lines"""
    prices = history['Close'].values
    dates = np.arange(len(prices))

    # Find local maxima and minima for trend lines
    from scipy.signal import argrelextrema

    # Get local maxima (resistance points)
    local_maxima = argrelextrema(prices, np.greater, order=5)[0]
    # Get local minima (support points)
    local_minima = argrelextrema(prices, np.less, order=5)[0]

    trend_lines = {}

    if len(local_maxima) >= 2:
        # Resistance trend line using last few peaks
        recent_maxima = local_maxima[-3:] if len(local_maxima) >= 3 else local_maxima
        max_dates = dates[recent_maxima]
        max_prices = prices[recent_maxima]

        if len(max_dates) >= 2:
            resistance_slope, resistance_intercept = np.polyfit(max_dates, max_prices, 1)
            trend_lines['resistance'] = {
                'slope': resistance_slope,
                'intercept': resistance_intercept,
                'dates': max_dates,
                'prices': max_prices
            }

    if len(local_minima) >= 2:
        # Support trend line using last few troughs
        recent_minima = local_minima[-3:] if len(local_minima) >= 3 else local_minima
        min_dates = dates[recent_minima]
        min_prices = prices[recent_minima]

        if len(min_dates) >= 2:
            support_slope, support_intercept = np.polyfit(min_dates, min_prices, 1)
            trend_lines['support'] = {
                'slope': support_slope,
                'intercept': support_intercept,
                'dates': min_dates,
                'prices': min_prices
            }

    return trend_lines

def generate_price_forecast(history: pd.DataFrame, forecast_days=15):
    """Generate price forecast using multiple models and confidence intervals"""

    # Prepare data
    prices = history['Close'].values
    volumes = history['Volume'].values if 'Volume' in history.columns else np.ones(len(prices))
    dates_numeric = np.arange(len(prices))

    # Feature engineering
    X = np.column_stack([
        dates_numeric,
        np.log(volumes + 1),  # Log volume
        np.roll(prices, 1),   # Previous day price
        np.roll(prices, 5),   # 5-day lag
    ])

    # Remove first 5 rows due to lag features
    X = X[5:]
    y = prices[5:]
    dates_numeric = dates_numeric[5:]

    # Remove any NaN or inf values
    mask = np.isfinite(X).all(axis=1) & np.isfinite(y)
    X = X[mask]
    y = y[mask]
    dates_numeric = dates_numeric[mask]

    forecasts = []

    # Model 1: Linear Regression with polynomial features
    try:
        poly_features = PolynomialFeatures(degree=2, include_bias=False)
        X_poly = poly_features.fit_transform(X)

        model1 = LinearRegression()
        model1.fit(X_poly, y)

        # Generate future features
        future_dates = np.arange(len(prices), len(prices) + forecast_days)
        last_price = prices[-1]
        last_volume = volumes[-1]

        future_X = []
        for i, future_date in enumerate(future_dates):
            if i == 0:
                prev_price = prices[-1]
                lag5_price = prices[-5] if len(prices) >= 5 else prices[-1]
            else:
                prev_price = forecasts[-1] if forecasts else last_price
                lag5_price = prices[-(5-i)] if (5-i) > 0 else (forecasts[i-5] if i >= 5 else last_price)

            future_X.append([
                future_date,
                np.log(last_volume + 1),
                prev_price,
                lag5_price
            ])

            if i == 0:  # First prediction
                future_X_poly = poly_features.transform([future_X[-1]])
                pred = model1.predict(future_X_poly)[0]
                forecasts.append(pred)

        # Generate all predictions at once for remaining days
        if len(forecasts) < forecast_days:
            for i in range(len(forecasts), forecast_days):
                future_X_poly = poly_features.transform([future_X[i]])
                pred = model1.predict(future_X_poly)[0]
                forecasts.append(pred)

    except Exception as e:
        print(f"Polynomial model failed: {e}")
        # Fallback to simple trend
        recent_trend = np.polyfit(range(min(30, len(prices))), prices[-min(30, len(prices)):], 1)
        for i in range(forecast_days):
            forecasts.append(recent_trend[1] + recent_trend[0] * (len(prices) + i))

    # Calculate confidence intervals based on recent volatility
    recent_returns = np.diff(np.log(prices[-30:])) if len(prices) >= 30 else np.diff(np.log(prices))
    volatility = np.std(recent_returns) * np.sqrt(252)  # Annualized volatility

    # Create expanding confidence intervals
    confidence_intervals = []
    for i in range(forecast_days):
        # Increase uncertainty over time
        time_factor = np.sqrt((i + 1) / 252)  # Square root of time scaling
        interval_width = forecasts[i] * volatility * time_factor * 1.96  # 95% confidence

        confidence_intervals.append({
            'lower': max(0, forecasts[i] - interval_width),
            'upper': forecasts[i] + interval_width
        })

    return forecasts, confidence_intervals

def create_candlestick_chart(history: pd.DataFrame, include_forecast=True):
    """Create enhanced candlestick chart with trend lines and forecasts"""

    fig = go.Figure()

    # Add candlestick chart
    fig.add_trace(go.Candlestick(
        x=history.index,
        open=history['Open'],
        high=history['High'],
        low=history['Low'],
        close=history['Close'],
        name="OHLC",
        increasing_line_color='#00ff88',
        decreasing_line_color='#ff4444'
    ))

    # Calculate and add trend lines
    trend_lines = calculate_trend_lines(history)

    if 'resistance' in trend_lines:
        resistance = trend_lines['resistance']
        start_idx = max(0, len(history) - 100)  # Show trend line for last 100 days
        end_idx = len(history) - 1

        start_price = resistance['slope'] * start_idx + resistance['intercept']
        end_price = resistance['slope'] * end_idx + resistance['intercept']

        fig.add_trace(go.Scatter(
            x=[history.index[start_idx], history.index[end_idx]],
            y=[start_price, end_price],
            mode='lines',
            line=dict(color='red', width=2, dash='dash'),
            name='Resistance Trend',
            showlegend=True
        ))

    if 'support' in trend_lines:
        support = trend_lines['support']
        start_idx = max(0, len(history) - 100)
        end_idx = len(history) - 1

        start_price = support['slope'] * start_idx + support['intercept']
        end_price = support['slope'] * end_idx + support['intercept']

        fig.add_trace(go.Scatter(
            x=[history.index[start_idx], history.index[end_idx]],
            y=[start_price, end_price],
            mode='lines',
            line=dict(color='green', width=2, dash='dash'),
            name='Support Trend',
            showlegend=True
        ))

    # Add price forecast if requested
    if include_forecast:
        try:
            forecasts, confidence_intervals = generate_price_forecast(history)

            # Create future dates
            last_date = history.index[-1]
            future_dates = pd.date_range(
                start=last_date + pd.Timedelta(days=1),
                periods=len(forecasts),
                freq='D'
            )

            # Add median forecast line
            fig.add_trace(go.Scatter(
                x=future_dates,
                y=forecasts,
                mode='lines',
                line=dict(color='orange', width=3),
                name='Median Forecast',
                showlegend=True
            ))

            # Add confidence interval area
            upper_bounds = [ci['upper'] for ci in confidence_intervals]
            lower_bounds = [ci['lower'] for ci in confidence_intervals]

            fig.add_trace(go.Scatter(
                x=list(future_dates) + list(future_dates[::-1]),
                y=upper_bounds + lower_bounds[::-1],
                fill='toself',
                fillcolor='rgba(255, 165, 0, 0.3)',
                line=dict(color='rgba(255, 165, 0, 0)'),
                name='Forecast Range (95% CI)',
                showlegend=True
            ))

            # Add connection line from last historical price to first forecast
            fig.add_trace(go.Scatter(
                x=[history.index[-1], future_dates[0]],
                y=[history['Close'].iloc[-1], forecasts[0]],
                mode='lines',
                line=dict(color='orange', width=2, dash='dot'),
                showlegend=False
            ))

        except Exception as e:
            print(f"Forecast generation failed: {e}")

    # Update layout
    fig.update_layout(
        title={
            'text': 'Enhanced Candlestick Chart with Trend Lines and Forecast',
            'x': 0.5,
            'font': {'size': 18}
        },
        xaxis_title='Date',
        yaxis_title='Price ($)',
        template='plotly_dark',
        height=700,
        showlegend=True,
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=0.01,
            bgcolor="rgba(0,0,0,0.5)"
        ),
        xaxis=dict(
            rangeslider=dict(visible=False),
            type='date'
        ),
        yaxis=dict(
            fixedrange=False
        )
    )

    return fig

def create_technical_indicators_chart(history: pd.DataFrame):
    """Create technical indicators visualization (RSI and MACD) - Enhanced version"""
    dates = history.index
    prices = history['Close']

    # Calculate RSI
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))

    # Calculate MACD
    exp1 = prices.ewm(span=12, adjust=False).mean()
    exp2 = prices.ewm(span=26, adjust=False).mean()
    macd = exp1 - exp2
    signal = macd.ewm(span=9, adjust=False).mean()
    histogram = macd - signal

    # Create figure with subplots
    fig = make_subplots(
        rows=3, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.03,
        subplot_titles=('Price with Moving Averages', 'RSI', 'MACD'),
        row_heights=[0.5, 0.25, 0.25]
    )

    # Add price and moving averages in top subplot
    fig.add_trace(go.Scatter(
        x=dates, y=prices,
        name='Close Price',
        line=dict(color='#1f77b4', width=2)
    ), row=1, col=1)

    fig.add_trace(go.Scatter(
        x=dates, y=exp1,
        name='EMA 12',
        line=dict(color='orange', width=1)
    ), row=1, col=1)

    fig.add_trace(go.Scatter(
        x=dates, y=exp2,
        name='EMA 26',
        line=dict(color='red', width=1)
    ), row=1, col=1)

    # Add RSI
    fig.add_trace(go.Scatter(
        x=dates, y=rsi,
        name='RSI',
        line=dict(color='purple', width=2)
    ), row=2, col=1)

    # Add MACD
    fig.add_trace(go.Scatter(
        x=dates, y=macd,
        name='MACD',
        line=dict(color='blue', width=2)
    ), row=3, col=1)

    fig.add_trace(go.Scatter(
        x=dates, y=signal,
        name='Signal',
        line=dict(color='red', width=2)
    ), row=3, col=1)

    # Add MACD histogram
    colors = ['green' if val >= 0 else 'red' for val in histogram]
    fig.add_trace(go.Bar(
        x=dates, y=histogram,
        name='MACD Histogram',
        marker_color=colors,
        opacity=0.6
    ), row=3, col=1)

    # Add RSI reference lines
    fig.add_hline(y=70, line_dash="dash", line_color="red", row=2, col=1)
    fig.add_hline(y=30, line_dash="dash", line_color="green", row=2, col=1)
    fig.add_hline(y=50, line_dash="dot", line_color="gray", row=2, col=1)

    # Add MACD zero line
    fig.add_hline(y=0, line_dash="solid", line_color="gray", row=3, col=1)

    # Update layout
    fig.update_layout(
        height=800,
        showlegend=True,
        title_text="Advanced Technical Indicators",
        template='plotly_dark'
    )

    return fig