#!/usr/bin/env python3
"""Run the PR05 incompatible/live/replay experiment with real ROS processes."""

import argparse
import os
from pathlib import Path
import shutil
import signal
import subprocess
import tempfile
import time

import yaml


TOPIC = '/robot_a/sensor_pose'


def command(*args, timeout=20):
    result = subprocess.run(args, text=True, capture_output=True, timeout=timeout)
    return f'$ {" ".join(args)}\nexit={result.returncode}\n{result.stdout}{result.stderr}', result


def launch(log_path, *args):
    log = log_path.open('w')
    child = subprocess.Popen(
        ['ros2', 'launch', 'course_bringup', 'patrol.launch.py',
         'namespace:=robot_a', *args],
        stdout=log, stderr=subprocess.STDOUT, start_new_session=True,
    )
    log.close()
    return child


def stop(child):
    if child.poll() is None:
        os.killpg(child.pid, signal.SIGINT)
        try:
            child.wait(timeout=12)
        except subprocess.TimeoutExpired:
            os.killpg(child.pid, signal.SIGTERM)
            child.wait(timeout=5)


def wait_for_topic(child, subscribers=1):
    deadline = time.monotonic() + 20
    while time.monotonic() < deadline:
        if child.poll() is not None:
            raise AssertionError(f'launch exited early: {child.returncode}')
        _, info = command('ros2', 'topic', 'info', TOPIC, '--verbose', timeout=6)
        if (info.returncode == 0 and 'Publisher count: 1' in info.stdout
                and f'Subscription count: {subscribers}' in info.stdout):
            return
        time.sleep(0.4)
    raise AssertionError(f'{TOPIC} did not reach expected graph state')


def wait_for_nodes(child, names):
    deadline = time.monotonic() + 20
    while time.monotonic() < deadline:
        if child.poll() is not None:
            raise AssertionError(f'launch exited early: {child.returncode}')
        _, result = command('ros2', 'node', 'list', timeout=6)
        if result.returncode == 0 and all(name in result.stdout.splitlines() for name in names):
            return
        time.sleep(0.4)
    raise AssertionError(f'ROS nodes did not appear: {names}')


def echo_once(reliability, seconds):
    return command('timeout', f'{seconds}s', 'ros2', 'topic', 'echo', TOPIC,
                   '--qos-reliability', reliability, '--once', timeout=seconds + 6)


def write_evidence(folder, name, text):
    if folder is not None:
        (folder / name).write_text(text, encoding='utf-8')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--evidence-dir', type=Path)
    args = parser.parse_args()
    evidence = args.evidence_dir
    if evidence is not None:
        evidence.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix='pr05-') as temp:
        temp = Path(temp)
        bag_dir = (evidence / 'bag' if evidence else temp / 'bag')
        if bag_dir.exists():
            suffix = 2
            while (evidence / f'bag-{suffix}').exists():
                suffix += 1
            bag_dir = evidence / f'bag-{suffix}'
        before_log = temp / 'reliable-launch.log'
        after_log = temp / 'best-effort-launch.log'
        replay_log = temp / 'replay.log'

        print('Starting incompatible reliable listener with record=false', flush=True)
        child = launch(before_log, 'record:=false', 'subscriber_reliability:=reliable')
        try:
            wait_for_topic(child)
            wait_for_nodes(child, ('/turtlesim', '/robot_a/patrol',
                                   '/robot_a/pose_relay', '/robot_a/pose_listener'))
            parts = []
            for cli in [('ros2', 'node', 'list'), ('ros2', 'topic', 'list', '-t'),
                        ('ros2', 'topic', 'info', TOPIC, '--verbose'),
                        ('ros2', 'topic', 'info', '/turtle1/cmd_vel', '--verbose')]:
                output, result = command(*cli)
                assert result.returncode == 0, output
                parts.append(output)
            assert all(name in parts[0] for name in
                       ('/turtlesim', '/robot_a/patrol', '/robot_a/pose_relay',
                        '/robot_a/pose_listener'))
            assert '/rosbag2_recorder' not in parts[0]
            assert TOPIC in parts[1]
            assert '/turtle1/cmd_vel' in parts[1] and '/robot_a/cmd_vel' not in parts[1]
            assert 'BEST_EFFORT' in parts[2].upper() and 'RELIABLE' in parts[2].upper()
            output, result = echo_once('reliable', 3)
            parts.append(output)
            assert result.returncode == 124 and not result.stdout.strip(), output
            print('PASS incompatible: visible topic, reliable echo timed out', flush=True)
        finally:
            stop(child)
        before_text = before_log.read_text()
        assert 'incompatible QoS' in before_text and 'received sensor_pose #' not in before_text
        parts.append('$ ros2 launch ... record:=false subscriber_reliability:=reliable\n'
                     + before_text)
        write_evidence(evidence, 'qos-before.txt', '\n'.join(parts))

        print('Starting compatible listener and MCAP recorder', flush=True)
        child = launch(after_log, 'record:=true', 'subscriber_reliability:=best_effort',
                       f'bag_dir:={bag_dir}')
        try:
            wait_for_topic(child, subscribers=2)
            wait_for_nodes(child, ('/rosbag2_recorder', '/turtlesim', '/robot_a/patrol',
                                   '/robot_a/pose_relay', '/robot_a/pose_listener'))
            after_parts = []
            for cli in [('ros2', 'node', 'list'), ('ros2', 'topic', 'list', '-t'),
                        ('ros2', 'topic', 'info', TOPIC, '--verbose')]:
                output, result = command(*cli)
                assert result.returncode == 0, output
                after_parts.append(output)
            assert '/rosbag2_recorder' in after_parts[0]
            output, result = echo_once('best_effort', 8)
            after_parts.append(output)
            assert result.returncode == 0 and 'x:' in result.stdout, output
            print('PASS live best_effort echo received Pose', flush=True)
            time.sleep(3)
        finally:
            stop(child)
        after_text = after_log.read_text()
        assert 'received sensor_pose #1' in after_text, after_text[-3000:]
        assert 'Recording...' in after_text or 'Recording' in after_text, after_text[-3000:]
        after_parts.append('$ ros2 launch ... record:=true subscriber_reliability:=best_effort\n'
                           + after_text)
        metadata = bag_dir / 'metadata.yaml'
        assert metadata.is_file() and len(list(bag_dir.glob('*.mcap'))) == 1
        recorded = yaml.safe_load(metadata.read_text())['rosbag2_bagfile_information']
        topics = recorded['topics_with_message_count']
        assert recorded['storage_identifier'] == 'mcap'
        assert len(topics) == 1 and topics[0]['topic_metadata']['name'] == TOPIC
        assert topics[0]['message_count'] > 0
        if evidence:
            shutil.copy2(metadata, evidence / 'bag-metadata.yaml')
        output, result = command('ros2', 'bag', 'info', str(bag_dir))
        assert result.returncode == 0 and TOPIC in result.stdout, output
        after_parts.append(output)
        print('PASS MCAP: one sensor topic and one .mcap file', flush=True)

        print('Replaying the same bag with best_effort override', flush=True)
        with replay_log.open('w') as log:
            replay = subprocess.Popen(
                ['ros2', 'bag', 'play', str(bag_dir), '-l',
                 '--qos-profile-overrides-path', 'config/qos-overrides.yaml'],
                stdout=log, stderr=subprocess.STDOUT, start_new_session=True,
            )
        try:
            wait_for_topic(replay, subscribers=0)
            output, result = echo_once('reliable', 3)
            after_parts.append(output)
            assert result.returncode == 124 and not result.stdout.strip(), output
            output, result = echo_once('best_effort', 8)
            after_parts.append(output)
            assert result.returncode == 0 and 'x:' in result.stdout, output
            print('PASS replay: reliable timed out, best_effort received Pose', flush=True)
        finally:
            stop(replay)
        after_parts.append('$ ros2 bag play ... --qos-profile-overrides-path '
                           'config/qos-overrides.yaml\n' + replay_log.read_text())
        write_evidence(evidence, 'qos-after.txt', '\n'.join(after_parts))
        print('PASS PR05 live and replay experiment', flush=True)


if __name__ == '__main__':
    main()
