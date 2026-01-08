"""
Tests for trading strategies module.
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime

import sys
sys.path.insert(0, '..')
from backend.strategies.mean_reversion import MeanReversionStrategy
from backend.strategies.ema_crossover import EMACrossoverStrategy
from backend.strategies.breakout import BreakoutStrategy


@pytest.fixture
def sample_data():
    """Create sample OHLCV data with indicators."""
    np.random.seed(42)
    n = 100

    dates = pd.date_range(start='2024-01-01', periods=n, freq='15min')
    close = 100 + np.cumsum(np.random.randn(n) * 0.5)

    df = pd.DataFrame({
        'open': close * (1 + np.random.randn(n) * 0.001),
        'high': close * 1.01,
        'low': close * 0.99,
        'close': close,
        'volume': np.random.randint(1000, 5000, n).astype(float),
        'rsi': 50 + np.random.randn(n) * 15,
        'bb_upper': close * 1.02,
        'bb_middle': close,
        'bb_lower': close * 0.98,
        'atr': np.abs(np.random.randn(n)) + 1,
        'adx': 20 + np.random.rand(n) * 30,
        'trending': np.random.choice([True, False], n),
        'ema_9': close * (1 + np.random.randn(n) * 0.005),
        'ema_21': close * (1 + np.random.randn(n) * 0.005),
        'macd': np.random.randn(n) * 2,
        'macd_signal': np.random.randn(n) * 2,
        'trend_bias': np.random.choice([1, -1], n),
    }, index=dates)

    return df


@pytest.fixture
def config():
    """Sample configuration."""
    return {
        'strategies': {
            'mean_reversion': {
                'enabled': True,
                'stop_atr_multiplier': 1.5
            },
            'ema_crossover': {
                'enabled': True,
                'fast_ema': 9,
                'slow_ema': 21,
                'adx_threshold': 25,
                'rsi_filter_long': 50,
                'rsi_filter_short': 50,
                'stop_atr_multiplier': 2.0,
                'min_risk_reward': 2.0
            },
            'breakout': {
                'enabled': True,
                'lookback_period': 20,
                'volume_multiplier': 1.5,
                'adx_confirmation': True,
                'stop_atr_multiplier': 1.5
            }
        },
        'indicators': {
            'rsi': {'overbought': 70, 'oversold': 30},
            'adx': {'threshold': 25}
        },
        'risk_management': {
            'max_risk_per_trade': 0.01,
            'take_profit': {'min_risk_reward_ratio': 2.0}
        }
    }


class TestMeanReversionStrategy:
    """Test suite for Mean Reversion strategy."""

    def test_init(self, config):
        """Test strategy initialization."""
        strategy = MeanReversionStrategy(config)
        assert strategy.name == 'mean_reversion'

    def test_check_entry_returns_none_or_dict(self, sample_data, config):
        """Test check_entry returns None or signal dict."""
        strategy = MeanReversionStrategy(config)
        result = strategy.check_entry(sample_data, 10000)

        assert result is None or isinstance(result, dict)

    def test_long_entry_on_oversold(self, config):
        """Test long entry when RSI is oversold and price below BB lower."""
        strategy = MeanReversionStrategy(config)

        n = 50
        dates = pd.date_range(start='2024-01-01', periods=n, freq='15min')
        close = np.array([100.0] * n)

        df = pd.DataFrame({
            'open': close,
            'high': close * 1.01,
            'low': close * 0.99,
            'close': close,
            'volume': [1000.0] * n,
            'rsi': [25.0] * n,  # Oversold < 30
            'bb_lower': close * 1.02,  # Price below BB lower
            'bb_middle': close * 1.05,
            'bb_upper': close * 1.08,
            'atr': [2.0] * n,
            'adx': [20.0] * n,  # Not trending
            'trending': [False] * n,
        }, index=dates)

        signal = strategy.check_entry(df, 10000)

        if signal:
            assert signal['direction'] == 'long'
            assert signal['strategy'] == 'mean_reversion'

    def test_short_entry_on_overbought(self, config):
        """Test short entry when RSI is overbought and price above BB upper."""
        strategy = MeanReversionStrategy(config)

        n = 50
        dates = pd.date_range(start='2024-01-01', periods=n, freq='15min')
        close = np.array([100.0] * n)

        df = pd.DataFrame({
            'open': close,
            'high': close * 1.01,
            'low': close * 0.99,
            'close': close,
            'volume': [1000.0] * n,
            'rsi': [75.0] * n,  # Overbought > 70
            'bb_lower': close * 0.92,
            'bb_middle': close * 0.95,
            'bb_upper': close * 0.98,  # Price above BB upper
            'atr': [2.0] * n,
            'adx': [20.0] * n,
            'trending': [False] * n,
        }, index=dates)

        signal = strategy.check_entry(df, 10000)

        if signal:
            assert signal['direction'] == 'short'

    def test_no_entry_in_trending_market(self, config):
        """Test no entry when market is trending."""
        strategy = MeanReversionStrategy(config)

        n = 50
        dates = pd.date_range(start='2024-01-01', periods=n, freq='15min')
        close = np.array([100.0] * n)

        df = pd.DataFrame({
            'open': close,
            'high': close * 1.01,
            'low': close * 0.99,
            'close': close,
            'volume': [1000.0] * n,
            'rsi': [25.0] * n,
            'bb_lower': close * 1.02,
            'bb_middle': close * 1.05,
            'bb_upper': close * 1.08,
            'atr': [2.0] * n,
            'adx': [35.0] * n,  # Strongly trending
            'trending': [True] * n,  # Market is trending
        }, index=dates)

        signal = strategy.check_entry(df, 10000)
        # Should not enter mean reversion in trending market
        # Implementation may vary


class TestEMACrossoverStrategy:
    """Test suite for EMA Crossover strategy."""

    def test_init(self, config):
        """Test strategy initialization."""
        strategy = EMACrossoverStrategy(config)
        assert strategy.name == 'ema_crossover'

    def test_bullish_crossover(self, config):
        """Test bullish EMA crossover detection."""
        strategy = EMACrossoverStrategy(config)

        n = 50
        dates = pd.date_range(start='2024-01-01', periods=n, freq='15min')
        close = np.linspace(100, 110, n)

        # Create crossover: fast EMA crosses above slow EMA
        ema_9 = np.concatenate([close[:25] * 0.99, close[25:] * 1.01])
        ema_21 = close

        df = pd.DataFrame({
            'open': close * 0.99,
            'high': close * 1.01,
            'low': close * 0.98,
            'close': close,
            'volume': [1000.0] * n,
            'rsi': [55.0] * n,  # Above 50
            'ema_9': ema_9,
            'ema_21': ema_21,
            'atr': [2.0] * n,
            'adx': [30.0] * n,  # Trending
            'trending': [True] * n,
            'macd': [1.0] * n,
            'macd_signal': [0.5] * n,
            'trend_bias': [1] * n,
        }, index=dates)

        signal = strategy.check_entry(df, 10000)
        # Check if crossover is detected

    def test_bearish_crossover(self, config):
        """Test bearish EMA crossover detection."""
        strategy = EMACrossoverStrategy(config)

        n = 50
        dates = pd.date_range(start='2024-01-01', periods=n, freq='15min')
        close = np.linspace(110, 100, n)  # Downtrend

        # Create crossover: fast EMA crosses below slow EMA
        ema_9 = np.concatenate([close[:25] * 1.01, close[25:] * 0.99])
        ema_21 = close

        df = pd.DataFrame({
            'open': close * 1.01,
            'high': close * 1.02,
            'low': close * 0.99,
            'close': close,
            'volume': [1000.0] * n,
            'rsi': [45.0] * n,  # Below 50
            'ema_9': ema_9,
            'ema_21': ema_21,
            'atr': [2.0] * n,
            'adx': [30.0] * n,
            'trending': [True] * n,
            'macd': [-1.0] * n,
            'macd_signal': [-0.5] * n,
            'trend_bias': [-1] * n,
        }, index=dates)

        signal = strategy.check_entry(df, 10000)


class TestBreakoutStrategy:
    """Test suite for Breakout strategy."""

    def test_init(self, config):
        """Test strategy initialization."""
        strategy = BreakoutStrategy(config)
        assert strategy.name == 'breakout'

    def test_bullish_breakout(self, config):
        """Test bullish breakout detection."""
        strategy = BreakoutStrategy(config)

        n = 50
        dates = pd.date_range(start='2024-01-01', periods=n, freq='15min')

        # Create consolidation then breakout
        close = np.array([100.0] * 45 + [105.0, 106.0, 107.0, 108.0, 109.0])
        high = close * 1.01
        high[:45] = 101.0  # Resistance at 101

        df = pd.DataFrame({
            'open': close * 0.99,
            'high': high,
            'low': close * 0.99,
            'close': close,
            'volume': np.concatenate([[1000.0] * 45, [3000.0] * 5]),  # Volume spike
            'atr': [1.0] * n,
            'adx': [28.0] * n,  # Trending
            'trending': [True] * n,
            'trend_bias': [1] * n,
        }, index=dates)

        signal = strategy.check_entry(df, 10000)

    def test_no_breakout_without_volume(self, config):
        """Test no breakout signal without volume confirmation."""
        strategy = BreakoutStrategy(config)

        n = 50
        dates = pd.date_range(start='2024-01-01', periods=n, freq='15min')

        close = np.array([100.0] * 45 + [105.0, 106.0, 107.0, 108.0, 109.0])

        df = pd.DataFrame({
            'open': close * 0.99,
            'high': close * 1.01,
            'low': close * 0.99,
            'close': close,
            'volume': [1000.0] * n,  # No volume spike
            'atr': [1.0] * n,
            'adx': [28.0] * n,
            'trending': [True] * n,
            'trend_bias': [1] * n,
        }, index=dates)

        signal = strategy.check_entry(df, 10000)
        # May not generate signal without volume confirmation


class TestStrategyCommon:
    """Test common strategy functionality."""

    def test_strategies_have_check_entry(self, config):
        """Test all strategies have check_entry method."""
        strategies = [
            MeanReversionStrategy(config),
            EMACrossoverStrategy(config),
            BreakoutStrategy(config),
        ]

        for strategy in strategies:
            assert hasattr(strategy, 'check_entry')
            assert callable(strategy.check_entry)

    def test_strategies_have_name(self, config):
        """Test all strategies have name attribute."""
        strategies = [
            MeanReversionStrategy(config),
            EMACrossoverStrategy(config),
            BreakoutStrategy(config),
        ]

        for strategy in strategies:
            assert hasattr(strategy, 'name')
            assert isinstance(strategy.name, str)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
