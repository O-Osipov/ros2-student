"""Bounds and atomic runtime updates for PR04."""

import math

import pytest
import rclpy
from rclpy.parameter import Parameter

from patrol.control import choose_command, validate_settings
from patrol.patrol import Patrol


@pytest.mark.parametrize('linear_speed,turn_rate,publish_hz', [
    (0.5, 0.3, 10.0),
    (0.5, 0.3, 5.0),
    (0.0, -1.0, 1.0),
    (1.0, 1.0, 30.0),
])
def test_valid_settings(linear_speed, turn_rate, publish_hz):
    assert validate_settings(linear_speed, turn_rate, publish_hz) == ''


@pytest.mark.parametrize('linear_speed,turn_rate,publish_hz,field', [
    (0.5, 0.3, 0.0, 'publish_hz'),
    (0.5, 0.3, -1.0, 'publish_hz'),
    (0.5, 0.3, math.nan, 'publish_hz'),
    (0.5, 0.3, math.inf, 'publish_hz'),
    (-0.1, 0.3, 10.0, 'linear_speed'),
    (0.5, 1.1, 10.0, 'turn_rate'),
    (True, 0.3, 10.0, 'linear_speed'),
])
def test_invalid_settings(linear_speed, turn_rate, publish_hz, field):
    assert field in validate_settings(linear_speed, turn_rate, publish_hz)


def test_accepted_speed_changes_command():
    assert choose_command(None, 0.8, -0.4) == (0.0, 0.0)
    assert choose_command(object(), 0.8, -0.4) == (0.8, -0.4)


def test_rejected_frequency_preserves_parameter_state_and_timer():
    rclpy.init()
    node = Patrol()
    try:
        initial_timer = node.timer
        assert initial_timer.timer_period_ns == 100_000_000
        result = node.set_parameters_atomically([
            Parameter('publish_hz', value=5.0),
            Parameter('linear_speed', value=0.8),
        ])
        assert result.successful
        assert node.timer is not initial_timer
        assert initial_timer not in node.timers
        assert node.timer.timer_period_ns == 200_000_000
        assert len(list(node.timers)) == 1
        assert node.publish_hz == node.get_parameter('publish_hz').value == 5.0
        assert node.linear_speed == 0.8
        accepted_timer = node.timer
        for bad_hz in (0.0, -1.0, math.nan):
            result = node.set_parameters_atomically([
                Parameter('publish_hz', value=bad_hz),
                Parameter('linear_speed', value=0.9),
            ])
            assert not result.successful
            assert 'publish_hz' in result.reason
            assert node.get_parameter('publish_hz').value == 5.0
            assert node.get_parameter('linear_speed').value == 0.8
            assert node.timer is accepted_timer
            assert len(list(node.timers)) == 1
    finally:
        node.destroy_node()
        rclpy.try_shutdown()
