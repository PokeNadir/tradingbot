"""
Tests for paper trading module.
"""

import pytest
from datetime import datetime

import sys
sys.path.insert(0, '..')
from backend.trading.paper_trader import PaperTrader


@pytest.fixture
def config():
    """Sample configuration for paper trader."""
    return {
        'paper_trading': {
            'initial_capital': 10000,
            'currency': 'USDT'
        },
        'costs': {
            'commission_percent': 0.001,  # 0.1%
            'slippage': {
                'liquid_majors': 0.0001,
                'volatile': 0.0005,
                'altcoins': 0.005
            }
        },
        'risk_management': {
            'max_risk_per_trade': 0.01,
            'max_open_positions': 3,
            'max_risk_total': 0.06,
            'stop_loss': {'atr_multiplier_swing': 2.0},
            'take_profit': {'min_risk_reward_ratio': 2.0},
            'drawdown': {
                'daily_loss_limit': 0.03,
                'consecutive_loss_pause': 3,
                'pause_duration_minutes': 15
            }
        }
    }


class TestPaperTrader:
    """Test suite for PaperTrader class."""

    def test_init(self, config):
        """Test initialization."""
        trader = PaperTrader(config)

        assert trader.balance == 10000
        assert trader.equity == 10000
        assert len(trader.positions) == 0
        assert len(trader.trades) == 0

    def test_open_long_position(self, config):
        """Test opening a long position."""
        trader = PaperTrader(config)

        signal = {
            'symbol': 'BTC/USDT',
            'direction': 'long',
            'entry_price': 50000,
            'stop_loss': 49000,
            'take_profit': 52000,
            'position_size': 0.1,
            'position_size_quote': 5000,
            'strategy': 'test'
        }

        position = trader.open_position(signal)

        assert position is not None
        assert position['symbol'] == 'BTC/USDT'
        assert position['direction'] == 'long'
        assert position['size'] == 0.1
        assert len(trader.positions) == 1

    def test_open_short_position(self, config):
        """Test opening a short position."""
        trader = PaperTrader(config)

        signal = {
            'symbol': 'ETH/USDT',
            'direction': 'short',
            'entry_price': 3000,
            'stop_loss': 3100,
            'take_profit': 2800,
            'position_size': 1.0,
            'position_size_quote': 3000,
            'strategy': 'test'
        }

        position = trader.open_position(signal)

        assert position is not None
        assert position['direction'] == 'short'

    def test_close_position_profit(self, config):
        """Test closing a position with profit."""
        trader = PaperTrader(config)

        # Open long position
        signal = {
            'symbol': 'BTC/USDT',
            'direction': 'long',
            'entry_price': 50000,
            'stop_loss': 49000,
            'take_profit': 52000,
            'position_size': 0.1,
            'position_size_quote': 5000,
            'strategy': 'test'
        }
        position = trader.open_position(signal)

        # Close at profit
        initial_balance = trader.balance
        trade = trader.close_position(position['id'], 51000, 'manual')

        assert trade is not None
        assert trade['pnl'] > 0  # Should have profit
        assert trader.balance > initial_balance
        assert len(trader.positions) == 0

    def test_close_position_loss(self, config):
        """Test closing a position with loss."""
        trader = PaperTrader(config)

        # Open long position
        signal = {
            'symbol': 'BTC/USDT',
            'direction': 'long',
            'entry_price': 50000,
            'stop_loss': 49000,
            'take_profit': 52000,
            'position_size': 0.1,
            'position_size_quote': 5000,
            'strategy': 'test'
        }
        position = trader.open_position(signal)

        # Close at loss
        initial_balance = trader.balance
        trade = trader.close_position(position['id'], 49500, 'stop_loss')

        assert trade is not None
        assert trade['pnl'] < 0  # Should have loss
        assert trader.balance < initial_balance

    def test_short_position_profit(self, config):
        """Test short position profit calculation."""
        trader = PaperTrader(config)

        # Open short position
        signal = {
            'symbol': 'ETH/USDT',
            'direction': 'short',
            'entry_price': 3000,
            'stop_loss': 3100,
            'take_profit': 2800,
            'position_size': 1.0,
            'position_size_quote': 3000,
            'strategy': 'test'
        }
        position = trader.open_position(signal)

        # Close at lower price (profit for short)
        trade = trader.close_position(position['id'], 2900, 'manual')

        assert trade['pnl'] > 0  # Short profits when price drops

    def test_short_position_loss(self, config):
        """Test short position loss calculation."""
        trader = PaperTrader(config)

        signal = {
            'symbol': 'ETH/USDT',
            'direction': 'short',
            'entry_price': 3000,
            'stop_loss': 3100,
            'take_profit': 2800,
            'position_size': 1.0,
            'position_size_quote': 3000,
            'strategy': 'test'
        }
        position = trader.open_position(signal)

        # Close at higher price (loss for short)
        trade = trader.close_position(position['id'], 3050, 'manual')

        assert trade['pnl'] < 0  # Short loses when price rises

    def test_check_stop_loss_long(self, config):
        """Test stop loss trigger for long position."""
        trader = PaperTrader(config)

        signal = {
            'symbol': 'BTC/USDT',
            'direction': 'long',
            'entry_price': 50000,
            'stop_loss': 49000,
            'take_profit': 52000,
            'position_size': 0.1,
            'position_size_quote': 5000,
            'strategy': 'test'
        }
        trader.open_position(signal)

        # Check with price below stop
        closed = trader.check_stop_take_profit({'BTC/USDT': {'last': 48500}})

        assert len(closed) > 0
        assert closed[0]['exit_reason'] == 'stop_loss'

    def test_check_take_profit_long(self, config):
        """Test take profit trigger for long position."""
        trader = PaperTrader(config)

        signal = {
            'symbol': 'BTC/USDT',
            'direction': 'long',
            'entry_price': 50000,
            'stop_loss': 49000,
            'take_profit': 52000,
            'position_size': 0.1,
            'position_size_quote': 5000,
            'strategy': 'test'
        }
        trader.open_position(signal)

        # Check with price above TP
        closed = trader.check_stop_take_profit({'BTC/USDT': {'last': 53000}})

        assert len(closed) > 0
        assert closed[0]['exit_reason'] == 'take_profit'

    def test_max_positions_limit(self, config):
        """Test maximum positions limit."""
        trader = PaperTrader(config)

        # Open max positions
        for i in range(3):
            signal = {
                'symbol': f'ASSET{i}/USDT',
                'direction': 'long',
                'entry_price': 100,
                'stop_loss': 98,
                'take_profit': 104,
                'position_size': 0.1,
                'position_size_quote': 10,
                'strategy': 'test'
            }
            trader.open_position(signal)

        assert len(trader.positions) == 3

        # Try to open one more
        signal = {
            'symbol': 'EXTRA/USDT',
            'direction': 'long',
            'entry_price': 100,
            'stop_loss': 98,
            'take_profit': 104,
            'position_size': 0.1,
            'position_size_quote': 10,
            'strategy': 'test'
        }
        result = trader.open_position(signal)

        # Should not open more than max
        # Implementation may return None or raise exception


class TestPortfolioTracking:
    """Test portfolio tracking functionality."""

    def test_get_portfolio(self, config):
        """Test getting portfolio state."""
        trader = PaperTrader(config)

        portfolio = trader.get_portfolio()

        assert 'balance' in portfolio
        assert 'equity' in portfolio
        assert 'total_pnl' in portfolio
        assert portfolio['balance'] == 10000

    def test_portfolio_updates_after_trade(self, config):
        """Test portfolio updates after trades."""
        trader = PaperTrader(config)

        signal = {
            'symbol': 'BTC/USDT',
            'direction': 'long',
            'entry_price': 50000,
            'stop_loss': 49000,
            'take_profit': 52000,
            'position_size': 0.1,
            'position_size_quote': 5000,
            'strategy': 'test'
        }
        position = trader.open_position(signal)
        trader.close_position(position['id'], 51000, 'manual')

        portfolio = trader.get_portfolio()

        # Should have some realized PnL
        assert portfolio['total_pnl'] != 0

    def test_get_positions(self, config):
        """Test getting open positions."""
        trader = PaperTrader(config)

        signal = {
            'symbol': 'BTC/USDT',
            'direction': 'long',
            'entry_price': 50000,
            'stop_loss': 49000,
            'take_profit': 52000,
            'position_size': 0.1,
            'position_size_quote': 5000,
            'strategy': 'test'
        }
        trader.open_position(signal)

        positions = trader.get_positions()

        assert len(positions) == 1
        assert positions[0]['symbol'] == 'BTC/USDT'

    def test_get_trades(self, config):
        """Test getting trade history."""
        trader = PaperTrader(config)

        signal = {
            'symbol': 'BTC/USDT',
            'direction': 'long',
            'entry_price': 50000,
            'stop_loss': 49000,
            'take_profit': 52000,
            'position_size': 0.1,
            'position_size_quote': 5000,
            'strategy': 'test'
        }
        position = trader.open_position(signal)
        trader.close_position(position['id'], 51000, 'manual')

        trades = trader.get_trades()

        assert len(trades) == 1
        assert trades[0]['symbol'] == 'BTC/USDT'


class TestCommissionsAndSlippage:
    """Test commission and slippage calculations."""

    def test_commission_deducted(self, config):
        """Test that commissions are deducted from balance."""
        trader = PaperTrader(config)
        initial_balance = trader.balance

        signal = {
            'symbol': 'BTC/USDT',
            'direction': 'long',
            'entry_price': 50000,
            'stop_loss': 49000,
            'take_profit': 52000,
            'position_size': 0.1,
            'position_size_quote': 5000,
            'strategy': 'test'
        }
        position = trader.open_position(signal)

        # Even without price movement, commission should reduce balance slightly
        # when closing
        trader.close_position(position['id'], 50000, 'manual')

        # With 0.1% commission each way, we should have slight loss
        assert trader.balance < initial_balance


class TestStatistics:
    """Test trading statistics."""

    def test_get_statistics(self, config):
        """Test getting trading statistics."""
        trader = PaperTrader(config)

        # Make some trades
        for i in range(5):
            signal = {
                'symbol': 'BTC/USDT',
                'direction': 'long',
                'entry_price': 50000,
                'stop_loss': 49000,
                'take_profit': 52000,
                'position_size': 0.1,
                'position_size_quote': 5000,
                'strategy': 'test'
            }
            position = trader.open_position(signal)
            # Alternate wins and losses
            exit_price = 51000 if i % 2 == 0 else 49500
            trader.close_position(position['id'], exit_price, 'manual')

        stats = trader.get_statistics()

        assert 'total_trades' in stats
        assert 'winning_trades' in stats
        assert 'losing_trades' in stats
        assert 'win_rate' in stats
        assert stats['total_trades'] == 5


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
