"""Relay the global turtle pose as a best-effort namespaced sensor stream."""

import rclpy
from rclpy.node import Node
from rclpy.qos import DurabilityPolicy, LivelinessPolicy, QoSProfile, ReliabilityPolicy

try:
    from turtlesim_msgs.msg import Pose  # Lyrical
except ImportError:
    from turtlesim.msg import Pose  # Jazzy


SENSOR_QOS = QoSProfile(
    depth=10,
    reliability=ReliabilityPolicy.BEST_EFFORT,
    durability=DurabilityPolicy.VOLATILE,
    liveliness=LivelinessPolicy.AUTOMATIC,
)


class PoseRelay(Node):
    def __init__(self):
        super().__init__('pose_relay')
        self.publisher = self.create_publisher(Pose, 'sensor_pose', SENSOR_QOS)
        self.subscription = self.create_subscription(
            Pose, 'turtle1/pose', self.publisher.publish, 10,
        )


def main(args=None):
    rclpy.init(args=args)
    node = PoseRelay()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()
