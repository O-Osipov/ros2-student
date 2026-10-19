"""PR04: publish a command from Pose using validated live parameters."""

import rclpy
from geometry_msgs.msg import Twist
from rcl_interfaces.msg import SetParametersResult
from rclpy.node import Node

from patrol.control import choose_command, validate_settings

try:
    from turtlesim_msgs.msg import Pose  # Lyrical
except ImportError:
    from turtlesim.msg import Pose  # Jazzy


class Patrol(Node):
    def __init__(self):
        super().__init__('patrol')
        self.declare_parameters('', [
            ('linear_speed', 0.5),
            ('turn_rate', 0.3),
            ('publish_hz', 10.0),
        ])
        self.linear_speed = self.get_parameter('linear_speed').value
        self.turn_rate = self.get_parameter('turn_rate').value
        self.publish_hz = self.get_parameter('publish_hz').value
        reason = validate_settings(self.linear_speed, self.turn_rate, self.publish_hz)
        if reason:
            raise ValueError(reason)
        self.latest_pose = None
        self.pose_sub = self.create_subscription(
            Pose, '/turtle1/pose', self.on_pose, 10,
        )
        self.publisher = self.create_publisher(Twist, 'cmd_vel', 10)
        self.timer = self.create_timer(1.0 / self.publish_hz, self.tick)
        self.add_on_set_parameters_callback(self.validate_parameters)
        self.add_post_set_parameters_callback(self.apply_parameters)

    def validate_parameters(self, parameters):
        candidate = {
            'linear_speed': self.linear_speed,
            'turn_rate': self.turn_rate,
            'publish_hz': self.publish_hz,
        }
        for parameter in parameters:
            if parameter.name in candidate:
                candidate[parameter.name] = parameter.value
        reason = validate_settings(**candidate)
        return SetParametersResult(successful=not reason, reason=reason)

    def apply_parameters(self, parameters):
        names = {parameter.name for parameter in parameters}
        if 'publish_hz' in names:
            new_hz = self.get_parameter('publish_hz').value
            if new_hz != self.publish_hz:
                self.timer.cancel()
                self.destroy_timer(self.timer)
                self.timer = self.create_timer(1.0 / new_hz, self.tick)
                self.publish_hz = new_hz
        if 'linear_speed' in names:
            self.linear_speed = self.get_parameter('linear_speed').value
        if 'turn_rate' in names:
            self.turn_rate = self.get_parameter('turn_rate').value

    def on_pose(self, message):
        self.latest_pose = message

    def tick(self):
        command = Twist()
        command.linear.x, command.angular.z = choose_command(
            self.latest_pose, self.linear_speed, self.turn_rate,
        )
        self.publisher.publish(command)


def main(args=None):
    rclpy.init(args=args)
    node = Patrol()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
