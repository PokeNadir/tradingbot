"""
Tests for risk management module.
"""

import pytest
from datetime import datetime, timedelta

import sys
sys.path.insert(0, '..')
from backend.trading.risk_manager import RiskManager, PositionSize, StopTakeProfit


@pytest.fixture
def config():
    """Sample risk management configuration."""
    return {
        'risk_management': {
            'max_risk_per_trade': 0.01,  # 1%
            'max_risk_per_trade_max': 0.02,  # 2% max
            'max_risk_per_day': 0.03,  # 3%
            'max_risk_total': 0.06,  # 6%
            'max_open_positions': 3,
            'default_leverage': 1,
            'kelly_fraction': 0.25,  # Quarter-Kelly
            'stop_loss': {
                'type': 'atr',
                'atr_multiplier_day': 1.5,
                'atr_multiplier_swing': 2.0,
                'atr_multiplier_position': 2.5,
                'atr_multiplier_volatile': 3.0,
                'fixed_percent': 0.02
            },
            'take_profit': {
                'min_risk_reward_ratio': 2.0,
                'trailing_stop': True,
                'trailing_atr_multiplier': 1.0,
                'scaling_out': {
                    'enabled': True,
                    'level_1_percent': 0.33,
                    'level_1_r': 1.0,
                    'level_2_percent': 0.33,
                    'level_2_r': 2.0,
                    'level_3_percent': 0.34
                }
            },
            'drawdown': {
                'daily_loss_limit': 0.03,
                'weekly_loss_limit': 0.06,
                'max_drawdown': 0.15,
                'consecutive_loss_pause': 3,
                'pause_duration_minutes': 15
            }
        }
    }


class TestRiskManager:
    """Test suite for RiskManager class."""

    def test_init(self, config):
        """Test initialization."""
        rm = RiskManager(config)
        assert rm.max_risk_per_trade == 0.01
        assert rm.max_open_positions == 3

    def test_calculate_position_size(self, config):
        """Test position size calculation."""
        rm = RiskManager(config)

        result = rm.calculate_position_size(
            capital=10000,
            entry_price=100,
            stop_loss=98,  # 2% stop
            win_rate=0.5,
            avg_win_loss_ratio=2.0
        )

        assert isinstance(result, PositionSize)
        assert result.size > 0
        assert result.size_quote > 0
        assert result.risk_amount > 0
        assert result.risk_percent <= rm.max_risk_per_trade

    def test_position_size_respects_max_risk(self, config):
        """Test that position size doesn't exceed max risk."""
        rm = RiskManager(config)

        result = rm.calculate_position_size(
            capital=10000,
            entry_price=100,
            stop_loss=99,  # 1% stop
            win_rate=0.5,
            avg_win_loss_ratio=2.0
        )

        # Risk amount should not exceed 1% of capital
        assert result.risk_amount <= 10000 * 0.01 * 1.01  # Small tolerance

    def test_position_size_with_tight_stop(self, config):
        """Test position size with very tight stop loss."""
        rm = RiskManager(config)

        result = rm.calculate_position_size(
            capital=10000,
            entry_price=100,
            stop_loss=99.9,  # 0.1% stop
            win_rate=0.5,
            avg_win_loss_ratio=2.0
        )

        # Position size should be larger with tighter stop
        assert result.size > 0
        assert result.risk_percent <= rm.max_risk_per_trade

    def test_position_size_with_wide_stop(self, config):
        """Test position size with wide stop loss."""
        rm = RiskManager(config)

        result = rm.calculate_position_size(
            capital=10000,
            entry_price=100,
            stop_loss=90,  # 10% stop
            win_rate=0.5,
            avg_win_loss_ratio=2.0
        )

        # Position size should be smaller with wider stop
        assert result.size > 0

    def test_calculate_stop_take_profit_long(self, config):
        """Test stop/take profit for long position."""
        rm = RiskManager(config)

        result = rm.calculate_stop_take_profit(
            entry_price=100,
            direction='long',
            atr=2,
            style='swing'
        )

        assert isinstance(result, StopTakeProfit)
        assert result.stop_loss < 100  # Stop below entry for long
        assert result.take_profit > 100  # TP above entry for long
        assert result.risk_reward >= 2.0

    def test_calculate_stop_take_profit_short(self, config):
        """Test stop/take profit for short position."""
        rm = RiskManager(config)

        result = rm.calculate_stop_take_profit(
            entry_price=100,
            direction='short',
            atr=2,
            style='swing'
        )

        assert result.stop_loss > 100  # Stop above entry for short
        assert result.take_profit < 100  # TP below entry for short
        assert result.risk_reward >= 2.0

    def test_stop_styles(self, config):
        """Test different trading styles affect stop distance."""
        rm = RiskManager(config)

        day = rm.calculate_stop_take_profit(100, 'long', 2, 'day')
        swing = rm.calculate_stop_take_profit(100, 'long', 2, 'swing')
        position = rm.calculate_stop_take_profit(100, 'long', 2, 'position')
        volatile = rm.calculate_stop_take_profit(100, 'long', 2, 'volatile')

        # Stops should be progressively wider
        assert day.stop_distance <= swing.stop_distance
        assert swing.stop_distance <= position.stop_distance
        assert position.stop_distance <= volatile.stop_distance


class TestPreTradeConditions:
    """Test pre-trade condition checks."""

    def test_check_pre_trade_conditions_pass(self, config):
        """Test passing pre-trade conditions."""
        rm = RiskManager(config)

        can_trade, reason = rm.check_pre_trade_conditions(
            capital=10000,
            current_positions=0,
            current_exposure=0.01,
            spread_percent=0.001
        )

        assert can_trade is True
        assert reason == "OK"

    def test_check_pre_trade_too_many_positions(self, config):
        """Test failing due to too many positions."""
        rm = RiskManager(config)

        can_trade, reason = rm.check_pre_trade_conditions(
            capital=10000,
            current_positions=3,  # Max is 3
            current_exposure=0.01,
            spread_percent=0.001
        )

        assert can_trade is False
        assert "positions" in reason.lower()

    def test_check_pre_trade_high_exposure(self, config):
        """Test failing due to high exposure."""
        rm = RiskManager(config)

        can_trade, reason = rm.check_pre_trade_conditions(
            capital=10000,
            current_positions=0,
            current_exposure=0.07,  # > 6% max
            spread_percent=0.001
        )

        assert can_trade is False
        assert "exposition" in reason.lower() or "exposure" in reason.lower()

    def test_check_pre_trade_high_spread(self, config):
        """Test failing due to high spread."""
        rm = RiskManager(config)

        can_trade, reason = rm.check_pre_trade_conditions(
            capital=10000,
            current_positions=0,
            current_exposure=0.01,
            spread_percent=0.005  # > 0.2% max
        )

        assert can_trade is False
        assert "spread" in reason.lower()

    def test_consecutive_losses_pause(self, config):
        """Test pause after consecutive losses."""
        rm = RiskManager(config)

        # Simulate 3 consecutive losses
        rm.update_trade_result(-100, 10000)
        rm.update_trade_result(-100, 9900)
        rm.update_trade_result(-100, 9800)

        assert rm.consecutive_losses == 3

        can_trade, reason = rm.check_pre_trade_conditions(
            capital=9700,
            current_positions=0,
            current_exposure=0,
            spread_percent=0.001
        )

        assert can_trade is False
        assert "perte" in reason.lower() or "loss" in reason.lower() or "pause" in reason.lower()


class TestTradeTracking:
    """Test trade result tracking."""

    def test_update_trade_result_win(self, config):
        """Test updating with winning trade."""
        rm = RiskManager(config)

        rm.update_trade_result(100, 10000)

        assert rm.daily_pnl == 100
        assert rm.consecutive_losses == 0

    def test_update_trade_result_loss(self, config):
        """Test updating with losing trade."""
        rm = RiskManager(config)

        rm.update_trade_result(-100, 10000)

        assert rm.daily_pnl == -100
        assert rm.consecutive_losses == 1

    def test_consecutive_losses_reset_on_win(self, config):
        """Test consecutive losses reset after win."""
        rm = RiskManager(config)

        rm.update_trade_result(-100, 10000)
        rm.update_trade_result(-100, 9900)
        assert rm.consecutive_losses == 2

        rm.update_trade_result(200, 9800)
        assert rm.consecutive_losses == 0

    def test_reset_daily_stats(self, config):
        """Test daily stats reset."""
        rm = RiskManager(config)

        rm.update_trade_result(-100, 10000)
        rm.update_trade_result(50, 9900)

        rm.reset_daily_stats()

        assert rm.daily_pnl == 0


class TestScalingOut:
    """Test scaling out level calculations."""

    def test_get_scaling_out_levels_long(self, config):
        """Test scaling out levels for long position."""
        rm = RiskManager(config)

        levels = rm.get_scaling_out_levels(
            entry_price=100,
            stop_loss=98,  # 2% stop = 2 points risk
            direction='long'
        )

        assert 'level_1' in levels
        assert 'level_2' in levels
        assert 'level_3' in levels

        # Level 1 at 1R
        assert levels['level_1']['price'] == 102
        # Level 2 at 2R
        assert levels['level_2']['price'] == 104
        # Level 3 at 3R
        assert levels['level_3']['price'] == 106

    def test_get_scaling_out_levels_short(self, config):
        """Test scaling out levels for short position."""
        rm = RiskManager(config)

        levels = rm.get_scaling_out_levels(
            entry_price=100,
            stop_loss=102,  # 2% stop = 2 points risk
            direction='short'
        )

        # Levels should be below entry for short
        assert levels['level_1']['price'] == 98
        assert levels['level_2']['price'] == 96
        assert levels['level_3']['price'] == 94


class TestRiskSummary:
    """Test risk summary functionality."""

    def test_get_risk_summary(self, config):
        """Test getting risk summary."""
        rm = RiskManager(config)

        rm.update_trade_result(-50, 10000)
        rm.update_trade_result(100, 9950)

        summary = rm.get_risk_summary(10050)

        assert 'daily_pnl' in summary
        assert 'daily_pnl_percent' in summary
        assert 'consecutive_losses' in summary
        assert 'is_paused' in summary
        assert 'max_risk_per_trade' in summary

        assert summary['daily_pnl'] == 50  # -50 + 100


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
