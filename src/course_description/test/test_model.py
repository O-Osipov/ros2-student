"""Validate the actual expanded robot tree and parameterized dimensions."""

import math
from pathlib import Path
import subprocess
import xml.etree.ElementTree as ET


MODEL = Path(__file__).resolve().parents[1] / 'urdf/vehicle.urdf.xacro'


def expanded(*args):
    return ET.fromstring(subprocess.check_output(['xacro', str(MODEL), *args], text=True))


def joints(root):
    return {joint.find('child').get('link'): joint for joint in root.findall('joint')}


def test_tree_and_sensor_placement():
    root = expanded()
    links = {link.get('name') for link in root.findall('link')}
    assert links == {'base_link', 'camera_link', 'lidar_link', 'imu_link',
                     'front_left_wheel_link', 'front_right_wheel_link',
                     'rear_left_wheel_link', 'rear_right_wheel_link'}
    assert len(root.findall('joint')) == len(links) - 1
    children = joints(root)
    assert set(children) == links - {'base_link'}
    for child in children:
        seen = set()
        current = child
        while current != 'base_link':
            assert current not in seen
            seen.add(current)
            current = children[current].find('parent').get('link')
            assert current in links
    for sensor in ('camera_link', 'lidar_link', 'imu_link'):
        joint = children[sensor]
        assert joint.find('parent').get('link') == 'base_link', f'{sensor} must attach to base_link'
        assert [float(x) for x in joint.find('origin').get('xyz').split()] == [0.28, 0, 0.38]


def test_geometry_inertia_and_parameter_overrides():
    root = expanded()
    for link in root.findall('link'):
        assert link.find('visual/geometry') is not None
        assert link.find('collision/geometry') is not None
        inertia = link.find('inertial/inertia')
        mass = float(link.find('inertial/mass').get('value'))
        axes = [float(inertia.get(axis)) for axis in ('ixx', 'iyy', 'izz')]
        assert mass > 0 and all(math.isfinite(v) and v > 0 for v in axes)
        assert all(axes[i] <= sum(axes) - axes[i] for i in range(3))
    assert root.find("link[@name='base_link']/visual/geometry/box").get('size') == '1.05 0.52 0.22'
    changed = expanded('wheel_base:=1.0', 'track_width:=0.7', 'wheel_radius:=0.15')
    wheel = changed.find("link[@name='front_left_wheel_link']/visual/geometry/cylinder")
    assert math.isclose(float(wheel.get('radius')), 0.15)
    left = joints(changed)['front_left_wheel_link'].find('origin').get('xyz').split()
    assert [float(x) for x in left] == [0.5, 0.35, 0]
