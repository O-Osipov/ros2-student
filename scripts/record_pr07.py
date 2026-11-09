#!/usr/bin/env python3
"""Record PR07 MCAP for at least 35 seconds of /clock simulation time."""

import argparse
from pathlib import Path
import signal
import subprocess
import time

import rclpy
from rosgraph_msgs.msg import Clock
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data

TOPICS = (
    '/vehicle/camera/image_raw', '/vehicle/scan', '/vehicle/imu',
    '/vehicle/odom', '/tf', '/tf_static', '/clock',
)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', default='fixtures/pr07-sensors')
    parser.add_argument('--sim-seconds', type=float, default=35.0)
    args = parser.parse_args()
    output = Path(args.output)
    if output.exists():
        raise SystemExit(f'refusing to overwrite {output}')
    rclpy.init()
    node = Node('pr07_bag_clock_observer')
    times = []
    subscriber = node.create_subscription(
        Clock, '/clock', lambda m: times.append(m.clock.sec + m.clock.nanosec / 1e9),
        qos_profile_sensor_data)
    log_path = Path('evidence/pr07/record.log')
    command = [
        'ros2', 'bag', 'record', '--storage', 'mcap', '--use-sim-time',
        '--qos-profile-overrides-path',
        'src/course_simulation/config/bag-qos.yaml',
        '-o', str(output), '--topics', *TOPICS,
    ]
    start_wall = time.monotonic()
    try:
        with log_path.open('w') as log:
            recorder = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT)
            start_sim = None
            while time.monotonic() - start_wall < 240:
                rclpy.spin_once(node, timeout_sec=0.1)
                if times and start_sim is None:
                    start_sim = times[-1]
                if start_sim is not None and times[-1] - start_sim >= args.sim_seconds:
                    break
                if recorder.poll() is not None:
                    raise RuntimeError(f'recorder exited early with {recorder.returncode}')
            else:
                raise TimeoutError('simulation did not advance sufficiently')
            print(f'elapsed simulation seconds: {times[-1] - start_sim:.3f}', flush=True)
    finally:
        if 'recorder' in locals() and recorder.poll() is None:
            recorder.send_signal(signal.SIGINT)
            try:
                recorder.wait(timeout=30)
            except subprocess.TimeoutExpired:
                recorder.kill()
                recorder.wait()
        node.destroy_node()
        rclpy.shutdown()
    if recorder.returncode != 0:
        raise SystemExit(f'recorder exit code {recorder.returncode}; see {log_path}')
    print(f'MCAP saved at {output}')


if __name__ == '__main__':
    main()
