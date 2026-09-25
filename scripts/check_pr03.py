#!/usr/bin/env python3
"""Повторить опыт ПР03 в установленном workspace. Вывод — в stdout."""
import math
import os
from pathlib import Path
import signal
import subprocess
import tempfile
import time

import rclpy
from geometry_msgs.msg import Twist
from rclpy.node import Node
from patrol.patrol import Pose


class Observer(Node):
    def __init__(self):
        super().__init__('pr03_observer')
        self.pose = None
        self.samples = []
        self.create_subscription(Pose, '/turtle1/pose', self.receive_pose, 10)

    def receive_pose(self, message):
        self.pose = message

    def receive_command(self, message):
        self.samples.append((time.monotonic(), message.linear.x, message.angular.z))

    def wait(self, predicate, seconds=12):
        end = time.monotonic() + seconds
        while not predicate() and time.monotonic() < end:
            rclpy.spin_once(self, timeout_sec=0.05)
        assert predicate(), 'Expected event did not arrive before timeout'

    def spin_for(self, seconds):
        end = time.monotonic() + seconds
        while time.monotonic() < end:
            rclpy.spin_once(self, timeout_sec=0.05)

    def coordinates(self):
        return [self.pose.x, self.pose.y, self.pose.theta]


def stop(child):
    if child.poll() is None:
        # ros2 run/launch forwards SIGINT to its child; do not send it twice.
        child.send_signal(signal.SIGINT)
        try:
            child.wait(timeout=10)
        except subprocess.TimeoutExpired:
            os.killpg(child.pid, signal.SIGKILL)
            child.wait()
            raise AssertionError('SIGINT did not stop process')


def cli(*args):
    command = ['ros2', *args]
    print('$', ' '.join(command), flush=True)
    result = subprocess.run(command, text=True, capture_output=True, timeout=20)
    print(result.stdout + result.stderr, flush=True)
    assert result.returncode == 0
    return result.stdout


def main():
    rclpy.init()
    observer = Observer()
    children = []
    with tempfile.TemporaryDirectory(prefix='pr03-') as directory:
        def launch(*args):
            command = ['ros2', *args]
            print('$', ' '.join(command), flush=True)
            path = Path(directory) / f'{len(children)}.log'
            with path.open('w') as log:
                child = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT,
                                         start_new_session=True,
                                         env={**os.environ, 'PYTHONUNBUFFERED': '1'})
            children.append((child, path))
            return child

        def finish_patrol(child):
            stop(child)
            assert child.returncode == 0, f'patrol exit: {child.returncode}'
            observer.wait(lambda: 'patrol' not in observer.get_node_names())

        try:
            observer.spin_for(1)
            assert observer.count_publishers('/turtle1/pose') == 0, 'Use an empty ROS domain'
            assert observer.count_publishers('/turtle1/cmd_vel') == 0
            command_sub = observer.create_subscription(Twist, '/turtle1/cmd_vel', observer.receive_command, 10)
            patrol = launch('run', 'patrol', 'patrol', '--ros-args', '-r', 'cmd_vel:=/turtle1/cmd_vel')
            observer.wait(lambda: len(observer.samples) >= 5)
            assert all(v == w == 0 for _, v, w in observer.samples)
            print('PASS no Pose: five zero Twist messages', flush=True)
            finish_patrol(patrol)
            observer.destroy_subscription(command_sub)

            simulator = launch('launch', 'turtle_bringup', 'sim.launch.py')
            observer.wait(lambda: observer.pose is not None)
            cli('topic', 'type', '/turtle1/pose')
            before = observer.coordinates()
            patrol = launch('run', 'patrol', 'patrol')
            observer.wait(lambda: observer.count_publishers('/cmd_vel') == 1)
            observer.wait(lambda: observer.count_subscribers('/turtle1/pose') >= 2)
            cli('node', 'info', '/patrol')
            broken_info = cli('topic', 'info', '/cmd_vel', '--verbose')
            assert 'Publisher count: 1' in broken_info and 'Subscription count: 0' in broken_info
            cli('topic', 'info', '/turtle1/cmd_vel', '--verbose')
            observer.spin_for(2)
            broken = observer.coordinates()
            assert all(abs(a-b) < 1e-5 for a, b in zip(before, broken))
            print(f'PASS defect: before={before}; after={broken}; pose unchanged', flush=True)
            finish_patrol(patrol)

            patrol = launch('run', 'patrol', 'patrol', '--ros-args', '-r', 'cmd_vel:=/turtle1/cmd_vel')
            observer.wait(lambda: observer.count_publishers('/turtle1/cmd_vel') == 1)
            cli('topic', 'info', '/turtle1/cmd_vel', '--verbose')
            command_sub = observer.create_subscription(Twist, '/turtle1/cmd_vel', observer.receive_command, 10)
            observer.spin_for(1)
            observer.samples.clear()
            hz = launch('topic', 'hz', '/turtle1/cmd_vel')
            start = time.monotonic()
            observer.spin_for(10)
            duration = time.monotonic() - start
            stop(hz)
            print('ros2 topic hz (10 second observation):\n' + children[-1][1].read_text(), flush=True)
            assert len(observer.samples) >= 80, len(observer.samples)
            rate = (len(observer.samples)-1)/(observer.samples[-1][0]-observer.samples[0][0])
            assert 8 <= rate <= 12, rate
            assert all(abs(v-0.5) < 1e-6 and abs(w-0.3) < 1e-6 for _, v, w in observer.samples)
            assert observer.count_publishers('/turtle1/cmd_vel') == 1
            after = observer.coordinates()
            assert math.hypot(after[0]-broken[0], after[1]-broken[1]) > 0.1
            print(f'PASS fix: {duration:.3f}s, {len(observer.samples)} messages, {rate:.3f} Hz, Twist=(0.5, 0.3)', flush=True)
            print(f'PASS motion: before={broken}; after={after}', flush=True)
            finish_patrol(patrol)
            observer.wait(lambda: observer.count_publishers('/turtle1/cmd_vel') == 0)
            observer.spin_for(2)
            resting = observer.coordinates()
            observer.spin_for(0.5)
            assert all(abs(a-b) < 1e-5 for a, b in zip(resting, observer.coordinates()))
            assert observer.pose.linear_velocity == observer.pose.angular_velocity == 0
            print(f'PASS SIGINT: patrol exited 0; no command publisher; watchdog stopped turtle at {resting}', flush=True)
            stop(simulator)
            assert simulator.returncode == 0
            observer.wait(lambda: 'turtlesim' not in observer.get_node_names())
            print('PASS PR03 live experiment', flush=True)
        except Exception:
            for _, path in children:
                print(f'Process {path.name}:\n{path.read_text()[-2500:]}', flush=True)
            raise
        finally:
            try:
                for child, _ in reversed(children):
                    stop(child)
            finally:
                observer.destroy_node()
                rclpy.try_shutdown()


if __name__ == '__main__':
    main()
