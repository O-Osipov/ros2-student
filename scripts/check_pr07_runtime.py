#!/usr/bin/env python3
"""Measure PR07 topic frames, stamps, rates and clock in a live simulation."""

import argparse
import json
import time

import rclpy
from nav_msgs.msg import Odometry
from rosgraph_msgs.msg import Clock
from sensor_msgs.msg import Image, Imu, LaserScan
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, DurabilityPolicy, qos_profile_sensor_data
from tf2_msgs.msg import TFMessage

SENSORS = {
    '/vehicle/camera/image_raw': (Image, 'sensor_msgs/msg/Image', 'camera_link', 15),
    '/vehicle/scan': (LaserScan, 'sensor_msgs/msg/LaserScan', 'lidar_link', 10),
    '/vehicle/imu': (Imu, 'sensor_msgs/msg/Imu', 'imu_link', 100),
    '/vehicle/odom': (Odometry, 'nav_msgs/msg/Odometry', 'odom', 50),
}


def ns(stamp):
    return stamp.sec * 1_000_000_000 + stamp.nanosec


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--seconds', type=float, default=15)
    args = parser.parse_args()
    rclpy.init()
    node = Node('pr07_observer')
    samples = {topic: [] for topic in SENSORS}
    frames = {topic: set() for topic in SENSORS}
    clock = []
    raw_frames = set()
    tf_dynamic = set()
    tf_static = set()
    subscriptions = []

    def on_sensor(topic, msg):
        samples[topic].append(ns(msg.header.stamp))
        frames[topic].add(msg.header.frame_id)
        if isinstance(msg, Odometry):
            frames[topic].add(msg.child_frame_id)

    def on_raw(msg):
        raw_frames.add((msg.header.frame_id, msg.child_frame_id))

    def on_tf(target, msg):
        target.update((t.header.frame_id, t.child_frame_id) for t in msg.transforms)

    for topic, (msg_type, _, _, _) in SENSORS.items():
        qos = qos_profile_sensor_data if topic != '/vehicle/odom' else QoSProfile(
            depth=10, reliability=ReliabilityPolicy.RELIABLE)
        subscriptions.append(node.create_subscription(
            msg_type, topic, lambda msg, topic=topic: on_sensor(topic, msg), qos))
    subscriptions.append(node.create_subscription(
        Odometry, '/vehicle/odom_gz', on_raw, QoSProfile(
            depth=10, reliability=ReliabilityPolicy.RELIABLE)))
    subscriptions.append(node.create_subscription(
        Clock, '/clock', lambda msg: clock.append(ns(msg.clock)), qos_profile_sensor_data))
    subscriptions.append(node.create_subscription(
        TFMessage, '/tf', lambda msg: on_tf(tf_dynamic, msg), QoSProfile(
            depth=10, reliability=ReliabilityPolicy.RELIABLE)))
    subscriptions.append(node.create_subscription(
        TFMessage, '/tf_static', lambda msg: on_tf(tf_static, msg), QoSProfile(
            depth=1, reliability=ReliabilityPolicy.RELIABLE,
            durability=DurabilityPolicy.TRANSIENT_LOCAL)))
    start = time.monotonic()
    try:
        while time.monotonic() - start < args.seconds:
            rclpy.spin_once(node, timeout_sec=0.05)
    finally:
        node.destroy_node()
        rclpy.shutdown()
    elapsed = time.monotonic() - start
    result = {
        'measurement_wall_seconds': round(elapsed, 3),
        'clock': {
            'messages': len(clock),
            'first_ns': clock[0] if clock else None,
            'last_ns': clock[-1] if clock else None,
            'real_time_factor': round((clock[-1]-clock[0])/1e9/elapsed, 3) if len(clock)>1 else None,
        },
        'sensors': {},
        'gazebo_odom_frames': sorted([list(x) for x in raw_frames]),
        'dynamic_tf_frames': sorted([list(x) for x in tf_dynamic]),
        'static_tf_frames': sorted([list(x) for x in tf_static]),
    }
    for topic, (_, msg_type, expected_frame, declared_hz) in SENSORS.items():
        stamps = samples[topic]
        span = (stamps[-1] - stamps[0])/1e9 if len(stamps)>1 else 0
        result['sensors'][topic] = {
            'type': msg_type,
            'frame_ids': sorted(frames[topic]),
            'expected_frame_id': expected_frame,
            'stamp_source': 'simulation /clock',
            'declared_hz': declared_hz,
            'measured_hz_sim': round((len(stamps)-1)/span, 2) if span>0 else None,
            'measured_hz_wall': round(len(stamps)/elapsed, 2),
            'messages': len(stamps),
            'first_stamp_ns': stamps[0] if stamps else None,
            'last_stamp_ns': stamps[-1] if stamps else None,
        }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    bad = [topic for topic in SENSORS if not samples[topic]]
    if not clock or bad or ('odom', 'base_link') not in tf_dynamic:
        raise SystemExit(f'missing clock/sensors/tf: {bad}')


if __name__ == '__main__':
    main()
