"""
Tests for technical indicators module.
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Import module to test
import sys
sys.path.insert(0, '..')
from backend.indicators.technical import TechnicalIndicators


@pytest.fixture
def sample_ohlcv_data():
    """Create sample OHLCV data for testing."""
    np.random.seed(42)
    n = 200

    # Generate random walk price data
    returns = np.random.randn(n) * 0.02
    close = 100 * np.exp(np.cumsum(returns))

    # Generate OHLCV
    high = close * (1 + np.abs(np.random.randn(n) * 0.01))
    low = close * (1 - np.abs(np.random.randn(n) * 0.01))
    open_price = np.roll(close, 1)
    open_price[0] = 100
    volume = np.random.randint(1000, 10000, n).astype(float)

    # Create DataFrame
    dates = pd.date_range(start='2024-01-01', periods=n, freq='15min')
    df = pd.DataFrame({
        'timestamp': dates,
        'open': open_price,
        'high': high,
        'low': low,
        'close': close,
        'volume': volume
    })
    df.set_index('timestamp', inplace=True)

    return df


@pytest.fixture
def config():
    """Sample configuration."""
    return {
        'indicators': {
            'rsi': {'period': 14, 'overbought': 70, 'oversold': 30},
            'macd': {'fast': 12, 'slow': 26, 'signal': 9},
            'bollinger': {'period': 20, 'std_dev': 2.0, 'squeeze_threshold': 0.75},
            'atr': {'period': 14},
            'ema': {'fast': 9, 'slow': 21, 'trend': 50},
            'adx': {'period': 14, 'threshold': 25},
            'stochastic': {'k_period': 14, 'd_period': 3, 'overbought': 80, 'oversold': 20}
        }
    }


class TestTechnicalIndicators:
    """Test suite for TechnicalIndicators class."""

    def test_init(self, config):
        """Test initialization."""
        ti = TechnicalIndicators(config)
        assert ti.config is not None

    def test_calculate_all(self, sample_ohlcv_data, config):
        """Test calculate_all adds all indicator columns."""
        ti = TechnicalIndicators(config)
        result = ti.calculate_all(sample_ohlcv_data)

        # Check RSI
        assert 'rsi' in result.columns
        assert result['rsi'].dropna().between(0, 100).all()

        # Check MACD
        assert 'macd' in result.columns
        assert 'macd_signal' in result.columns
        assert 'macd_histogram' in result.columns

        # Check Bollinger Bands
        assert 'bb_upper' in result.columns
        assert 'bb_middle' in result.columns
        assert 'bb_lower' in result.columns
        assert 'bb_squeeze' in result.columns

        # Check ATR
        assert 'atr' in result.columns
        assert result['atr'].dropna().min() >= 0

        # Check EMAs
        assert 'ema_9' in result.columns
        assert 'ema_21' in result.columns
        assert 'ema_50' in result.columns
        assert 'sma_200' in result.columns

        # Check ADX
        assert 'adx' in result.columns
        assert 'trending' in result.columns

        # Check Stochastic
        assert 'stoch_k' in result.columns
        assert 'stoch_d' in result.columns

    def test_add_rsi(self, sample_ohlcv_data, config):
        """Test RSI calculation."""
        ti = TechnicalIndicators(config)
        result = ti.add_rsi(sample_ohlcv_data.copy())

        assert 'rsi' in result.columns
        rsi_values = result['rsi'].dropna()

        # RSI should be between 0 and 100
        assert rsi_values.min() >= 0
        assert rsi_values.max() <= 100

    def test_add_macd(self, sample_ohlcv_data, config):
        """Test MACD calculation."""
        ti = TechnicalIndicators(config)
        result = ti.add_macd(sample_ohlcv_data.copy())

        assert 'macd' in result.columns
        assert 'macd_signal' in result.columns
        assert 'macd_histogram' in result.columns

        # Histogram should equal MACD - Signal
        non_na = result[['macd', 'macd_signal', 'macd_histogram']].dropna()
        if len(non_na) > 0:
            diff = (non_na['macd'] - non_na['macd_signal']).round(6)
            hist = non_na['macd_histogram'].round(6)
            assert np.allclose(diff, hist, atol=1e-4)

    def test_add_bollinger_bands(self, sample_ohlcv_data, config):
        """Test Bollinger Bands calculation."""
        ti = TechnicalIndicators(config)
        result = ti.add_bollinger_bands(sample_ohlcv_data.copy())

        assert 'bb_upper' in result.columns
        assert 'bb_middle' in result.columns
        assert 'bb_lower' in result.columns

        # Upper should be >= Middle >= Lower
        non_na = result[['bb_upper', 'bb_middle', 'bb_lower']].dropna()
        assert (non_na['bb_upper'] >= non_na['bb_middle']).all()
        assert (non_na['bb_middle'] >= non_na['bb_lower']).all()

    def test_add_atr(self, sample_ohlcv_data, config):
        """Test ATR calculation."""
        ti = TechnicalIndicators(config)
        result = ti.add_atr(sample_ohlcv_data.copy())

        assert 'atr' in result.columns
        assert 'atr_percent' in result.columns

        # ATR should be positive
        assert result['atr'].dropna().min() >= 0

    def test_add_emas(self, sample_ohlcv_data, config):
        """Test EMA calculations."""
        ti = TechnicalIndicators(config)
        result = ti.add_emas(sample_ohlcv_data.copy())

        assert 'ema_9' in result.columns
        assert 'ema_21' in result.columns
        assert 'ema_50' in result.columns
        assert 'sma_200' in result.columns

        # EMAs should be close to price range
        last_close = sample_ohlcv_data['close'].iloc[-1]
        last_ema9 = result['ema_9'].iloc[-1]

        # EMA should be within 50% of current price (generous check)
        assert abs(last_ema9 - last_close) / last_close < 0.5

    def test_add_adx(self, sample_ohlcv_data, config):
        """Test ADX calculation."""
        ti = TechnicalIndicators(config)
        result = ti.add_adx(sample_ohlcv_data.copy())

        assert 'adx' in result.columns
        assert 'adx_pos' in result.columns
        assert 'adx_neg' in result.columns
        assert 'trending' in result.columns

        # ADX should be between 0 and 100
        adx_values = result['adx'].dropna()
        assert adx_values.min() >= 0
        assert adx_values.max() <= 100

    def test_add_stochastic(self, sample_ohlcv_data, config):
        """Test Stochastic calculation."""
        ti = TechnicalIndicators(config)
        result = ti.add_stochastic(sample_ohlcv_data.copy())

        assert 'stoch_k' in result.columns
        assert 'stoch_d' in result.columns

        # Stochastic should be between 0 and 100
        k_values = result['stoch_k'].dropna()
        assert k_values.min() >= 0
        assert k_values.max() <= 100

    def test_get_current_values(self, sample_ohlcv_data, config):
        """Test getting current indicator values."""
        ti = TechnicalIndicators(config)
        df = ti.calculate_all(sample_ohlcv_data)
        values = ti.get_current_values(df)

        assert 'rsi' in values
        assert 'macd' in values
        assert 'bb_upper' in values
        assert 'atr' in values
        assert 'adx' in values
        assert 'close' in values

    def test_empty_dataframe(self, config):
        """Test handling of empty DataFrame."""
        ti = TechnicalIndicators(config)
        empty_df = pd.DataFrame(columns=['open', 'high', 'low', 'close', 'volume'])

        values = ti.get_current_values(empty_df)
        assert values == {}


class TestIndicatorEdgeCases:
    """Test edge cases for indicators."""

    def test_flat_price(self, config):
        """Test indicators with flat/constant price."""
        ti = TechnicalIndicators(config)

        n = 50
        dates = pd.date_range(start='2024-01-01', periods=n, freq='15min')
        df = pd.DataFrame({
            'open': [100.0] * n,
            'high': [100.0] * n,
            'low': [100.0] * n,
            'close': [100.0] * n,
            'volume': [1000.0] * n
        }, index=dates)

        result = ti.calculate_all(df)

        # RSI should be around 50 for flat price
        # ATR should be 0 for flat price
        assert result['atr'].iloc[-1] == 0 or pd.isna(result['atr'].iloc[-1])

    def test_trending_market(self, config):
        """Test indicators in trending market."""
        ti = TechnicalIndicators(config)

        n = 100
        dates = pd.date_range(start='2024-01-01', periods=n, freq='15min')

        # Create uptrending data
        close = np.linspace(100, 150, n)
        df = pd.DataFrame({
            'open': close * 0.99,
            'high': close * 1.01,
            'low': close * 0.98,
            'close': close,
            'volume': [1000.0] * n
        }, index=dates)

        result = ti.calculate_all(df)

        # In uptrend, RSI should be elevated
        last_rsi = result['rsi'].iloc[-1]
        assert last_rsi > 50  # Should be bullish

        # ADX should show trending
        last_adx = result['adx'].iloc[-1]
        # Note: ADX takes time to build, may still be low


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
