"""Pure command selection and bounds for the patrol parameters."""

import math


PARAMETER_BOUNDS = {
    'linear_speed': (0.0, 1.0),
    'turn_rate': (-1.0, 1.0),
    'publish_hz': (1.0, 30.0),
}


def validate_settings(linear_speed, turn_rate, publish_hz):
    """Return an error for invalid settings, or an empty string if valid."""
    values = {
        'linear_speed': linear_speed,
        'turn_rate': turn_rate,
        'publish_hz': publish_hz,
    }
    for name, value in values.items():
        lower, upper = PARAMETER_BOUNDS[name]
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            return f'{name} must be a finite number in [{lower}, {upper}]'
        if not math.isfinite(value) or not lower <= value <= upper:
            return f'{name} must be a finite number in [{lower}, {upper}]'
    return ''


def choose_command(pose, linear_speed=0.5, turn_rate=0.3):
    """Stop before the first pose; otherwise use the accepted speeds."""
    if pose is None:
        return 0.0, 0.0
    return linear_speed, turn_rate
