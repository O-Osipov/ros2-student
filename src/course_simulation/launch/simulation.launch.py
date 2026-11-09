"""Run the course world, one bridge, and the two ROS adapters."""

import os
from pathlib import Path

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess, GroupAction, SetEnvironmentVariable
from launch.conditions import IfCondition, UnlessCondition
from launch.substitutions import Command, LaunchConfiguration
from launch_ros.actions import Node, PushRosNamespace


def generate_launch_description():
    share = Path(get_package_share_directory('course_simulation'))
    description = Path(get_package_share_directory('course_description'))
    model_path = str(share / 'models')
    existing = os.environ.get('GZ_SIM_RESOURCE_PATH', '')
    resource_path = model_path + (':' + existing if existing else '')
    robot_description = Command(['xacro ', str(description / 'urdf/vehicle.urdf.xacro')])
    gazebo_base = ['gz', 'sim', '-s', '-r']
    tf_remaps = [('tf', '/tf'), ('tf_static', '/tf_static')]
    return LaunchDescription([
        DeclareLaunchArgument('world', default_value=str(share / 'worlds/mcity-minimal.sdf')),
        DeclareLaunchArgument('bridge_config', default_value=str(share / 'config/bridge.yaml')),
        DeclareLaunchArgument('headless', default_value='true'),
        DeclareLaunchArgument('namespace', default_value='simulation'),
        SetEnvironmentVariable('GZ_SIM_RESOURCE_PATH', resource_path),
        ExecuteProcess(cmd=gazebo_base + ['--headless-rendering', LaunchConfiguration('world')],
                       output='screen', condition=IfCondition(LaunchConfiguration('headless'))),
        ExecuteProcess(cmd=gazebo_base + [LaunchConfiguration('world')],
                       output='screen', condition=UnlessCondition(LaunchConfiguration('headless'))),
        GroupAction([
            PushRosNamespace(LaunchConfiguration('namespace')),
            Node(package='robot_state_publisher', executable='robot_state_publisher',
                 name='robot_state_publisher', output='screen', remappings=tf_remaps,
                 parameters=[{'robot_description': robot_description, 'use_sim_time': True}]),
            Node(package='ros_gz_bridge', executable='parameter_bridge',
                 name='bridge', output='screen',
                 parameters=[{'config_file': LaunchConfiguration('bridge_config')}]),
            Node(package='course_simulation', executable='drive_adapter',
                 output='screen', parameters=[{'use_sim_time': True}]),
            Node(package='course_simulation', executable='odom_adapter',
                 output='screen', remappings=tf_remaps,
                 parameters=[{'use_sim_time': True}]),
        ]),
    ])
