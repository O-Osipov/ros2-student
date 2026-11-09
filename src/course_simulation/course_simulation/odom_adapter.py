"""Normalize Gazebo odometry and own the sole dynamic odom->base_link tf."""

from copy import deepcopy
import math

import rclpy
from geometry_msgs.msg import TransformStamped
from nav_msgs.msg import Odometry
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy
from tf2_ros import TransformBroadcaster

SOURCE_PARENT = 'course_ackermann/odom'
SOURCE_CHILD = 'course_ackermann/base_link'


def normalize_odometry(message: Odometry):
    """Return normalized odometry and tf; reject foreign frames or nonfinite data."""
    if message.header.frame_id != SOURCE_PARENT or message.child_frame_id != SOURCE_CHILD:
        raise ValueError('unexpected Gazebo odometry frames')
    p = message.pose.pose
    t = message.twist.twist
    numbers = (
        p.position.x, p.position.y, p.position.z,
        p.orientation.x, p.orientation.y, p.orientation.z, p.orientation.w,
        t.linear.x, t.linear.y, t.linear.z,
        t.angular.x, t.angular.y, t.angular.z,
        *message.pose.covariance, *message.twist.covariance,
    )
    if not all(math.isfinite(x) for x in numbers):
        raise ValueError('non-finite Gazebo odometry')
    output = deepcopy(message)
    output.header.frame_id = 'odom'
    output.child_frame_id = 'base_link'
    transform = TransformStamped()
    transform.header = deepcopy(output.header)
    transform.child_frame_id = 'base_link'
    transform.transform.translation.x = p.position.x
    transform.transform.translation.y = p.position.y
    transform.transform.translation.z = p.position.z
    transform.transform.rotation = deepcopy(p.orientation)
    return output, transform


class OdomAdapter(Node):
    def __init__(self):
        super().__init__('odom_adapter')
        qos = QoSProfile(depth=10, reliability=ReliabilityPolicy.RELIABLE)
        self.publisher = self.create_publisher(Odometry, '/vehicle/odom', qos)
        self.broadcaster = TransformBroadcaster(self)
        self.subscription = self.create_subscription(
            Odometry, '/vehicle/odom_gz', self.on_odometry, qos)

    def on_odometry(self, message):
        try:
            normalized, transform = normalize_odometry(message)
        except ValueError as error:
            self.get_logger().warn(f'odometry rejected: {error}')
            return
        self.publisher.publish(normalized)
        self.broadcaster.sendTransform(transform)


def main():
    rclpy.init()
    node = OdomAdapter()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    except RuntimeError:
        # Lyrical can fail to take an in-flight DDS sample during shutdown.
        if rclpy.ok():
            raise
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
