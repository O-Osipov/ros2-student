"""Convert validated Ackermann commands into Gazebo Twist commands."""

import math

import rclpy
from ackermann_msgs.msg import AckermannDriveStamped
from geometry_msgs.msg import Twist
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy

MAX_AGE_NS = 250_000_000
FUTURE_TOLERANCE_NS = 50_000_000
WHEEL_BASE_M = 0.8


def to_twist(command: AckermannDriveStamped, now_ns: int):
    """Return (Twist, reason); invalid input always yields a zero Twist."""
    result = Twist()
    stamp = command.header.stamp.sec * 1_000_000_000 + command.header.stamp.nanosec
    if now_ns <= 0 or stamp <= 0:
        return result, 'simulation clock or command stamp unavailable'
    age = now_ns - stamp
    if age > MAX_AGE_NS:
        return result, 'stale command'
    if age < -FUTURE_TOLERANCE_NS:
        return result, 'command stamp in the future'
    speed = command.drive.speed
    steering = command.drive.steering_angle
    if not math.isfinite(speed) or not math.isfinite(steering):
        return result, 'non-finite speed or steering angle'
    v = min(max(speed, 0.0), 1.2)
    delta = min(max(steering, -0.45), 0.45)
    result.linear.x = v
    result.angular.z = v * math.tan(delta) / WHEEL_BASE_M
    return result, None


class DriveAdapter(Node):
    def __init__(self):
        super().__init__('drive_adapter')
        qos = QoSProfile(depth=10, reliability=ReliabilityPolicy.RELIABLE)
        self.publisher = self.create_publisher(Twist, '/vehicle/gz_cmd_vel', qos)
        self.subscription = self.create_subscription(
            AckermannDriveStamped, '/drive/safe', self.on_command, qos)

    def on_command(self, command):
        converted, reason = to_twist(command, self.get_clock().now().nanoseconds)
        self.publisher.publish(converted)
        if reason:
            self.get_logger().warn(f'zero command: {reason}')


def main():
    rclpy.init()
    node = DriveAdapter()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
