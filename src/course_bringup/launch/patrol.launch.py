"""Start turtlesim, patrol, a sensor relay, listener and optional MCAP bag."""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess, GroupAction, LogInfo
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node, PushRosNamespace


def generate_launch_description():
    namespace = LaunchConfiguration('namespace')
    record = LaunchConfiguration('record')
    bag_dir = LaunchConfiguration('bag_dir')
    reliability = LaunchConfiguration('subscriber_reliability')

    return LaunchDescription([
        DeclareLaunchArgument('namespace', default_value='robot_a'),
        DeclareLaunchArgument('record', default_value='false'),
        DeclareLaunchArgument('bag_dir', default_value='/tmp/pr05-robot-a-bag'),
        DeclareLaunchArgument('subscriber_reliability', default_value='reliable'),
        LogInfo(msg=['PR05 namespace=/', namespace, ', record=', record,
                     ', bag_dir=', bag_dir, ', subscriber_reliability=', reliability]),
        Node(package='turtlesim', executable='turtlesim_node',
             name='turtlesim', output='screen'),
        GroupAction([
            PushRosNamespace(namespace),
            Node(package='patrol', executable='patrol', output='screen',
                 remappings=[('turtle1/pose', '/turtle1/pose'),
                             ('cmd_vel', '/turtle1/cmd_vel')]),
            Node(package='course_bringup', executable='pose_relay', output='screen',
                 remappings=[('turtle1/pose', '/turtle1/pose')]),
            Node(package='course_bringup', executable='pose_listener', output='screen',
                 parameters=[{'subscriber_reliability': reliability}]),
        ]),
        ExecuteProcess(
            cmd=['ros2', 'bag', 'record', '-s', 'mcap', '-o', bag_dir,
                 '--topics', ['/', namespace, '/sensor_pose']],
            output='screen',
            condition=IfCondition(record),
        ),
    ])
