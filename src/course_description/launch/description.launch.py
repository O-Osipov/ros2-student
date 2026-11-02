from pathlib import Path

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition
from launch.substitutions import Command, LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    model = Path(get_package_share_directory('course_description')) / 'urdf/vehicle.urdf.xacro'
    rviz_config = Path(get_package_share_directory('course_description')) / 'rviz/vehicle.rviz'
    description = Command(['xacro ', str(model)])
    return LaunchDescription([
        DeclareLaunchArgument('use_sim_time', default_value='false'),
        DeclareLaunchArgument('rviz', default_value='false'),
        Node(package='robot_state_publisher', executable='robot_state_publisher',
             name='robot_state_publisher', output='screen',
             parameters=[{'robot_description': description,
                          'use_sim_time': LaunchConfiguration('use_sim_time')}]),
        Node(package='rviz2', executable='rviz2', output='screen',
             arguments=['-d', str(rviz_config)],
             condition=IfCondition(LaunchConfiguration('rviz'))),
    ])
