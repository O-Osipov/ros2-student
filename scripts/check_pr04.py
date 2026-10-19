#!/usr/bin/env python3
"""Exercise live patrol parameters against real turtlesim, without a GUI."""

import math
import os
from pathlib import Path
import subprocess
import tempfile
import time

import rclpy
from geometry_msgs.msg import Twist

from check_pr03 import Observer, stop


def run(*command, timeout=20):
    print('$', ' '.join(command), flush=True)
    result = subprocess.run(command, text=True, capture_output=True, timeout=timeout)
    print(f'exit={result.returncode}', flush=True)
    print(result.stdout.strip(), flush=True)
    if result.stderr.strip():
        print('stderr:', result.stderr.strip(), flush=True)
    return result


def wait_for_parameter():
    deadline = time.monotonic() + 20
    while time.monotonic() < deadline:
        result = run('ros2', 'param', 'get', '/patrol', 'publish_hz', timeout=6)
        if result.returncode == 0 and '10.0' in result.stdout:
            return
        time.sleep(0.3)
    raise AssertionError('Parameter service did not become available')


def rate(samples):
    assert len(samples) >= 2, samples
    return (len(samples) - 1) / (samples[-1][0] - samples[0][0])


def main():
    rclpy.init()
    observer = Observer()
    children = []
    with tempfile.TemporaryDirectory(prefix='pr04-') as directory:
        def launch(*command):
            print('$', ' '.join(command), flush=True)
            path = Path(directory) / f'{len(children)}.log'
            with path.open('w') as log:
                child = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT,
                                         start_new_session=True, env=os.environ.copy())
            children.append((child, path))
            return child

        try:
            observer.spin_for(1)
            assert observer.count_publishers('/turtle1/pose') == 0, 'Use an empty ROS domain'
            simulator = launch('ros2', 'launch', 'turtle_bringup', 'sim.launch.py')
            observer.wait(lambda: observer.pose is not None)
            patrol = launch('ros2', 'run', 'patrol', 'patrol', '--ros-args',
                            '-r', 'cmd_vel:=/turtle1/cmd_vel')
            observer.wait(lambda: observer.count_publishers('/turtle1/cmd_vel') == 1)
            subscription = observer.create_subscription(
                Twist, '/turtle1/cmd_vel', observer.receive_command, 10)
            observer.wait(lambda: len(observer.samples) >= 5)
            wait_for_parameter()
            observer.spin_for(0.5)  # drain samples queued during a CLI call
            observer.samples.clear()
            observer.spin_for(2.2)
            initial_rate = rate(observer.samples)
            assert 8 <= initial_rate <= 12, initial_rate
            assert all(math.isclose(linear, 0.5) and math.isclose(turn, 0.3)
                       for _, linear, turn in observer.samples)
            print(f'PASS defaults: {len(observer.samples)} messages, {initial_rate:.3f} Hz, Twist=(0.5, 0.3)', flush=True)

            for name, value in (('linear_speed', '0.7'), ('turn_rate', '-0.2'),
                                ('publish_hz', '5.0')):
                result = run('ros2', 'param', 'set', '/patrol', name, value)
                assert result.returncode == 0 and 'successful' in result.stdout.lower(), result
            observer.spin_for(0.5)  # drain samples queued during a CLI call
            observer.samples.clear()
            observer.spin_for(3.2)
            updated_rate = rate(observer.samples)
            assert 4 <= updated_rate <= 6, updated_rate
            assert all(math.isclose(linear, 0.7) and math.isclose(turn, -0.2)
                       for _, linear, turn in observer.samples)
            print(f'PASS update: {len(observer.samples)} messages, {updated_rate:.3f} Hz, Twist=(0.7, -0.2)', flush=True)

            for bad in ('0.0', '-1.0'):
                result = run('ros2', 'param', 'set', '/patrol', 'publish_hz', bad)
                assert 'failed' in (result.stdout + result.stderr).lower(), result
                unchanged = run('ros2', 'param', 'get', '/patrol', 'publish_hz')
                assert unchanged.returncode == 0 and '5.0' in unchanged.stdout
                observer.spin_for(0.5)  # drain samples queued during a CLI call
                observer.samples.clear()
                observer.spin_for(2.2)
                retained_rate = rate(observer.samples)
                assert 4 <= retained_rate <= 6, retained_rate
                print(f'PASS reject {bad}: value=5.0, stream={retained_rate:.3f} Hz', flush=True)

            stop(patrol)
            assert patrol.returncode == 0
            observer.spin_for(2)
            resting = observer.coordinates()
            observer.spin_for(0.5)
            assert all(abs(a-b) < 1e-5 for a, b in zip(resting, observer.coordinates()))
            clear = run('ros2', 'service', 'call', '/clear', 'std_srvs/srv/Empty', '{}')
            assert clear.returncode == 0 and 'response' in clear.stdout.lower()
            actions = run('ros2', 'action', 'list', '-t')
            assert actions.returncode == 0
            assert '/turtle1/rotate_absolute [turtlesim_msgs/action/RotateAbsolute]' in actions.stdout
            print('PASS /clear service and /turtle1/rotate_absolute action discovery', flush=True)
            observer.destroy_subscription(subscription)
            stop(simulator)
            assert simulator.returncode == 0
            print('PASS PR04 live experiment', flush=True)
        except Exception:
            for _, path in children:
                print(f'Process {path.name}:\n{path.read_text()[-2000:]}', flush=True)
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
