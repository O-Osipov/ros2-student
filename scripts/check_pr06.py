#!/usr/bin/env python3
"""Observe the real static transform publisher and late QoS subscribers."""

import argparse
import os
from pathlib import Path
import signal
import subprocess
import tempfile
import time


def run(*command, timeout=15, cwd=None):
    result = subprocess.run(command, text=True, capture_output=True, timeout=timeout, cwd=cwd)
    return f'$ {" ".join(command)}\nexit={result.returncode}\n{result.stdout}{result.stderr}\n', result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--evidence-dir', type=Path)
    args = parser.parse_args()
    if args.evidence_dir:
        args.evidence_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='pr06-') as tmp:
        log = Path(tmp) / 'launch.log'
        with log.open('w') as stream:
            launch = subprocess.Popen(
                ['ros2', 'launch', 'course_description', 'description.launch.py'],
                stdout=stream, stderr=subprocess.STDOUT, start_new_session=True,
            )
        try:
            deadline = time.monotonic() + 20
            while time.monotonic() < deadline:
                if launch.poll() is not None:
                    raise AssertionError(log.read_text())
                _, info = run('ros2', 'topic', 'info', '/tf_static', '--verbose')
                if info.returncode == 0 and 'Publisher count: 1' in info.stdout:
                    break
                time.sleep(0.4)
            else:
                raise AssertionError('robot_state_publisher did not publish /tf_static')
            time.sleep(1)  # both echo processes must be late subscribers
            lines = []
            output, info = run('ros2', 'topic', 'info', '/tf_static', '--verbose')
            lines.append(output)
            assert 'Reliability: RELIABLE' in info.stdout
            assert 'Durability: TRANSIENT_LOCAL' in info.stdout
            for durability, expected in [('transient_local', 0), ('volatile', 124)]:
                output, result = run(
                    'timeout', '4s', 'ros2', 'topic', 'echo', '/tf_static', '--once',
                    '--qos-durability', durability, '--qos-reliability', 'reliable',
                    timeout=10,
                )
                lines.append(output)
                assert result.returncode == expected, output
                if durability == 'transient_local':
                    assert 'lidar_link' in result.stdout and 'base_link' in result.stdout
                else:
                    assert not result.stdout.strip(), output
            lines.append(
                'The fixed sensor transforms are published once with reliable, '
                'transient_local QoS. A late transient_local reader receives the '
                'retained sample; a late volatile reader receives no historical sample. '
                'Dynamic /tf uses volatile QoS because its transforms change over time.\n'
            )
            if args.evidence_dir:
                (args.evidence_dir / 'tf-qos.txt').write_text('\n'.join(lines))
            print('PASS /tf_static late-subscriber QoS', flush=True)
            output, tf = run('timeout', '6s', 'ros2', 'run', 'tf2_ros', 'tf2_echo',
                             'base_link', 'lidar_link', timeout=10)
            assert '0.280' in output or '0.28' in output, output
            print('PASS tf2_echo base_link lidar_link', flush=True)
            output2, frames = run('ros2', 'run', 'tf2_tools', 'view_frames',
                                  timeout=20, cwd=tmp)
            assert frames.returncode == 0, output2
            print('PASS view_frames', flush=True)
            if args.evidence_dir:
                (args.evidence_dir / 'tf-tools.txt').write_text(output + '\n' + output2)
        finally:
            if launch.poll() is None:
                os.killpg(launch.pid, signal.SIGINT)
                try:
                    launch.wait(timeout=8)
                except subprocess.TimeoutExpired:
                    os.killpg(launch.pid, signal.SIGTERM)
                    launch.wait(timeout=5)
            if args.evidence_dir:
                (args.evidence_dir / 'launch.txt').write_text(log.read_text())


if __name__ == '__main__':
    main()
