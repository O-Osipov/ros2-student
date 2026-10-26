"""The deliberately incompatible and corrected QoS profiles."""

from rclpy.qos import QoSCompatibility, qos_check_compatible

from course_bringup.pose_listener import listener_qos
from course_bringup.pose_relay import SENSOR_QOS


def test_reliable_request_cannot_match_best_effort_sensor():
    assert qos_check_compatible(SENSOR_QOS, listener_qos('reliable'))[0] == QoSCompatibility.ERROR


def test_best_effort_request_matches_sensor():
    assert qos_check_compatible(SENSOR_QOS, listener_qos('best_effort'))[0] == QoSCompatibility.OK
