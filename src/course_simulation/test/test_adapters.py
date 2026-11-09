import math

import pytest
from ackermann_msgs.msg import AckermannDriveStamped
from nav_msgs.msg import Odometry

from course_simulation.drive_adapter import to_twist
from course_simulation.odom_adapter import normalize_odometry

NOW = 10_000_000_000


def command(speed=1.0, steering=0.0, stamp_ns=NOW):
    msg = AckermannDriveStamped()
    msg.header.stamp.sec = stamp_ns // 1_000_000_000
    msg.header.stamp.nanosec = stamp_ns % 1_000_000_000
    msg.drive.speed = speed
    msg.drive.steering_angle = steering
    return msg


def test_straight_and_clamping():
    twist, reason = to_twist(command(speed=2.0), NOW)
    assert reason is None
    assert twist.linear.x == pytest.approx(1.2)
    assert twist.angular.z == 0.0


def test_turn_formula_and_steering_clamp():
    twist, reason = to_twist(command(speed=1.0, steering=2.0), NOW)
    assert reason is None
    assert twist.linear.x == 1.0
    assert twist.angular.z == pytest.approx(math.tan(0.45) / 0.8)


def test_zero_and_reverse_do_not_spin():
    for speed in (0.0, -1.0):
        twist, reason = to_twist(command(speed=speed, steering=0.3), NOW)
        assert reason is None
        assert twist.linear.x == twist.angular.z == 0.0


@pytest.mark.parametrize('msg,now,reason', [
    (command(stamp_ns=NOW - 250_000_001), NOW, 'stale'),
    (command(speed=float('nan')), NOW, 'non-finite'),
    (command(steering=float('inf')), NOW, 'non-finite'),
    (command(), 0, 'clock'),
    (command(stamp_ns=NOW + 100_000_000), NOW, 'future'),
])
def test_invalid_command_emits_zero(msg, now, reason):
    twist, actual = to_twist(msg, now)
    assert reason in actual
    assert twist.linear.x == twist.angular.z == 0.0


def source_odometry():
    msg = Odometry()
    msg.header.frame_id = 'course_ackermann/odom'
    msg.child_frame_id = 'course_ackermann/base_link'
    msg.header.stamp.sec = 12
    msg.header.stamp.nanosec = 345
    msg.pose.pose.position.x = 2.5
    msg.pose.pose.orientation.w = 1.0
    msg.twist.twist.linear.x = 0.8
    msg.pose.covariance[0] = 0.3
    msg.twist.covariance[0] = 0.4
    return msg


def test_normalization_preserves_payload_and_stamp():
    source = source_odometry()
    output, transform = normalize_odometry(source)
    assert output.header.frame_id == transform.header.frame_id == 'odom'
    assert output.child_frame_id == transform.child_frame_id == 'base_link'
    assert output.header.stamp == transform.header.stamp == source.header.stamp
    assert output.pose == source.pose
    assert output.twist == source.twist
    assert transform.transform.translation.x == 2.5
    assert transform.transform.rotation.w == 1.0
    assert source.header.frame_id == 'course_ackermann/odom'


def test_rejects_foreign_frames_and_nonfinite_values():
    msg = source_odometry()
    msg.child_frame_id = 'other/base_link'
    with pytest.raises(ValueError, match='frames'):
        normalize_odometry(msg)
    msg = source_odometry()
    msg.pose.covariance[3] = float('nan')
    with pytest.raises(ValueError, match='non-finite'):
        normalize_odometry(msg)
    msg = source_odometry()
    msg.twist.twist.angular.z = float('inf')
    with pytest.raises(ValueError, match='non-finite'):
        normalize_odometry(msg)
