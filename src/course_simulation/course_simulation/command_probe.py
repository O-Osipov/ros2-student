"""Publish a stamped test command to /drive/safe, then send zero."""

import argparse
import time

import rclpy
from ackermann_msgs.msg import AckermannDriveStamped
from rclpy.node import Node
from rclpy.parameter import Parameter
from rclpy.qos import QoSProfile, ReliabilityPolicy


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--speed', type=float, default=0.4)
    parser.add_argument('--steering', type=float, default=0.0)
    parser.add_argument('--seconds', type=float, default=4.0)
    args = parser.parse_args()
    rclpy.init()
    node = Node('command_probe', parameter_overrides=[Parameter('use_sim_time', value=True)],
                automatically_declare_parameters_from_overrides=True)
    publisher = node.create_publisher(
        AckermannDriveStamped, '/drive/safe',
        QoSProfile(depth=10, reliability=ReliabilityPolicy.RELIABLE))
    try:
        deadline = time.monotonic() + 10
        while node.get_clock().now().nanoseconds <= 0 and time.monotonic() < deadline:
            rclpy.spin_once(node, timeout_sec=0.1)
        if node.get_clock().now().nanoseconds <= 0:
            raise RuntimeError('/clock unavailable')
        deadline = time.monotonic() + args.seconds
        while time.monotonic() < deadline:
            message = AckermannDriveStamped()
            message.header.stamp = node.get_clock().now().to_msg()
            message.drive.speed = args.speed
            message.drive.steering_angle = args.steering
            publisher.publish(message)
            rclpy.spin_once(node, timeout_sec=0.1)
        message = AckermannDriveStamped()
        message.header.stamp = node.get_clock().now().to_msg()
        publisher.publish(message)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
