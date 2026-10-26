"""Observe the relay with selectable requested reliability."""

import rclpy
from rclpy.node import Node
from rclpy.qos import DurabilityPolicy, LivelinessPolicy, QoSProfile, ReliabilityPolicy

try:
    from turtlesim_msgs.msg import Pose  # Lyrical
except ImportError:
    from turtlesim.msg import Pose  # Jazzy


def listener_qos(reliability):
    if reliability not in ('reliable', 'best_effort'):
        raise ValueError('subscriber_reliability must be reliable or best_effort')
    return QoSProfile(
        depth=10,
        reliability=(ReliabilityPolicy.RELIABLE if reliability == 'reliable'
                     else ReliabilityPolicy.BEST_EFFORT),
        durability=DurabilityPolicy.VOLATILE,
        liveliness=LivelinessPolicy.AUTOMATIC,
    )


class PoseListener(Node):
    def __init__(self):
        super().__init__('pose_listener')
        self.declare_parameter('subscriber_reliability', 'reliable')
        reliability = self.get_parameter('subscriber_reliability').value
        self.count = 0
        self.subscription = self.create_subscription(
            Pose, 'sensor_pose', self.on_pose, listener_qos(reliability),
        )
        self.get_logger().info(f'Listening to sensor_pose with {reliability} reliability')

    def on_pose(self, message):
        self.count += 1
        if self.count == 1 or self.count % 20 == 0:
            self.get_logger().info(
                f'received sensor_pose #{self.count}: x={message.x:.3f}, y={message.y:.3f}',
            )


def main(args=None):
    rclpy.init(args=args)
    node = PoseListener()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()
