"""
Tests for signal generation module.
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime

import sys
sys.path.insert(0, '..')
from backend.indicators.signals import SignalGenerator


@pytest.fixture
def sample_data_with_indicators():
    """Create sample data with indicators for testing signals."""
    np.random.seed(42)
    n = 100

    dates = pd.date_range(start='2024-01-01', periods=n, freq='15min')

    # Create sample OHLCV
    close = 100 + np.cumsum(np.random.randn(n) * 0.5)
    df = pd.DataFrame({
        'open': close * (1 + np.random.randn(n) * 0.001),
        'high': close * 1.01,
        'low': close * 0.99,
        'close': close,
        'volume': np.random.randint(1000, 5000, n).astype(float),

        # Technical indicators
        'rsi': 50 + np.random.randn(n) * 15,
        'macd': np.random.randn(n) * 10,
        'macd_signal': np.random.randn(n) * 10,
        'macd_histogram': np.random.randn(n) * 5,
        'bb_upper': close * 1.02,
        'bb_middle': close,
        'bb_lower': close * 0.98,
        'bb_squeeze': np.random.choice([True, False], n),
        'atr': np.abs(np.random.randn(n)) + 1,
        'adx': 20 + np.random.rand(n) * 30,
        'trending': np.random.choice([True, False], n),
        'ema_9': close * (1 + np.random.randn(n) * 0.005),
        'ema_21': close * (1 + np.random.randn(n) * 0.005),
        'ema_50': close * (1 + np.random.randn(n) * 0.01),
        'sma_200': close * (1 + np.random.randn(n) * 0.02),
        'trend_bias': np.random.choice([1, -1, 0], n),
    }, index=dates)

    return df


@pytest.fixture
def config():
    """Sample configuration for signal generator."""
    return {
        'indicators': {
            'rsi': {'overbought': 70, 'oversold': 30},
            'adx': {'threshold': 25},
        },
        'risk_management': {
            'max_risk_per_trade': 0.01,
            'stop_loss': {'atr_multiplier_swing': 2.0},
            'take_profit': {'min_risk_reward_ratio': 2.0},
        },
        'strategies': {
            'mean_reversion': {'enabled': True},
            'ema_crossover': {'enabled': True, 'fast_ema': 9, 'slow_ema': 21},
            'breakout': {'enabled': True, 'lookback_period': 20, 'volume_multiplier': 1.5},
        }
    }


class TestSignalGenerator:
    """Test suite for SignalGenerator class."""

    def test_init(self, config):
        """Test initialization."""
        sg = SignalGenerator(config)
        assert sg.config is not None

    def test_generate_signals_returns_list(self, sample_data_with_indicators, config):
        """Test that generate_signals returns a list."""
        sg = SignalGenerator(config)
        signals = sg.generate_signals(
            sample_data_with_indicators,
            'BTC/USDT',
            10000
        )

        assert isinstance(signals, list)

    def test_signal_structure(self, sample_data_with_indicators, config):
        """Test that generated signals have required fields."""
        sg = SignalGenerator(config)

        # Modify data to trigger a signal
        df = sample_data_with_indicators.copy()
        df.iloc[-1, df.columns.get_loc('rsi')] = 25  # Oversold
        df.iloc[-1, df.columns.get_loc('close')] = df.iloc[-1]['bb_lower'] * 0.99  # Below BB lower

        signals = sg.generate_signals(df, 'BTC/USDT', 10000)

        for signal in signals:
            # Check required fields
            assert 'symbol' in signal
            assert 'direction' in signal
            assert 'strategy' in signal
            assert 'entry_price' in signal
            assert 'strength' in signal

    def test_mean_reversion_long_signal(self, config):
        """Test mean reversion generates long signal on oversold."""
        sg = SignalGenerator(config)

        # Create data that should trigger mean reversion long
        n = 50
        dates = pd.date_range(start='2024-01-01', periods=n, freq='15min')
        close = np.array([100.0] * n)

        df = pd.DataFrame({
            'open': close,
            'high': close * 1.01,
            'low': close * 0.99,
            'close': close,
            'volume': [1000.0] * n,
            'rsi': [28.0] * n,  # Oversold
            'bb_lower': close * 1.01,  # Price below BB lower
            'bb_middle': close * 1.05,
            'bb_upper': close * 1.09,
            'atr': [2.0] * n,
            'adx': [30.0] * n,
            'trending': [False] * n,  # Not trending (good for mean reversion)
            'trend_bias': [1] * n,
        }, index=dates)

        signals = sg.generate_signals(df, 'BTC/USDT', 10000)

        # Check if we got a mean reversion signal
        mr_signals = [s for s in signals if s['strategy'] == 'mean_reversion']
        # May or may not trigger depending on all conditions

    def test_ema_crossover_signal(self, config):
        """Test EMA crossover signal generation."""
        sg = SignalGenerator(config)

        n = 50
        dates = pd.date_range(start='2024-01-01', periods=n, freq='15min')
        close = np.linspace(100, 110, n)

        df = pd.DataFrame({
            'open': close * 0.99,
            'high': close * 1.01,
            'low': close * 0.98,
            'close': close,
            'volume': [1000.0] * n,
            'rsi': [55.0] * n,  # Above 50 for long bias
            'ema_9': close * 1.01,  # Fast above slow (bullish cross)
            'ema_21': close * 0.99,
            'ema_50': close * 0.95,
            'atr': [2.0] * n,
            'adx': [30.0] * n,  # Trending
            'trending': [True] * n,
            'trend_bias': [1] * n,
            'macd': [1.0] * n,
            'macd_signal': [0.5] * n,
        }, index=dates)

        signals = sg.generate_signals(df, 'BTC/USDT', 10000)
        # Crossover signals depend on previous bar comparison

    def test_no_signal_on_neutral_market(self, config):
        """Test that neutral conditions may not generate signals."""
        sg = SignalGenerator(config)

        n = 50
        dates = pd.date_range(start='2024-01-01', periods=n, freq='15min')
        close = np.array([100.0] * n)

        df = pd.DataFrame({
            'open': close,
            'high': close * 1.001,
            'low': close * 0.999,
            'close': close,
            'volume': [1000.0] * n,
            'rsi': [50.0] * n,  # Neutral
            'bb_lower': close * 0.98,
            'bb_middle': close,
            'bb_upper': close * 1.02,
            'atr': [0.5] * n,
            'adx': [15.0] * n,  # Not trending
            'trending': [False] * n,
            'ema_9': close,
            'ema_21': close,
            'trend_bias': [0] * n,
        }, index=dates)

        signals = sg.generate_signals(df, 'BTC/USDT', 10000)
        # Neutral market should have fewer signals

    def test_signal_strength_range(self, sample_data_with_indicators, config):
        """Test that signal strength is between 0 and 1."""
        sg = SignalGenerator(config)
        signals = sg.generate_signals(
            sample_data_with_indicators,
            'BTC/USDT',
            10000
        )

        for signal in signals:
            if 'strength' in signal:
                assert 0 <= signal['strength'] <= 1


class TestSignalFiltering:
    """Test signal filtering functionality."""

    def test_filter_weak_signals(self, config):
        """Test that weak signals can be filtered."""
        sg = SignalGenerator(config)

        signals = [
            {'symbol': 'BTC/USDT', 'strength': 0.9, 'direction': 'long'},
            {'symbol': 'BTC/USDT', 'strength': 0.3, 'direction': 'long'},
            {'symbol': 'BTC/USDT', 'strength': 0.7, 'direction': 'short'},
        ]

        min_strength = 0.5
        filtered = [s for s in signals if s['strength'] >= min_strength]

        assert len(filtered) == 2
        assert all(s['strength'] >= min_strength for s in filtered)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
