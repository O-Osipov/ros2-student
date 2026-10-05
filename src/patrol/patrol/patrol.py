"""ПР03: подписка хранит позу, таймер публикует команду каждые 0,1 с."""
import rclpy
from geometry_msgs.msg import Twist
from rclpy.node import Node

from patrol.control import choose_command

try:
    from turtlesim_msgs.msg import Pose  # Lyrical
except ImportError:
    from turtlesim.msg import Pose  # Jazzy


class Patrol(Node):
    def __init__(self):
        super().__init__('patrol')
        self.latest_pose = None
        self.pose_sub = self.create_subscription(
            Pose, '/turtle1/pose', self.on_pose, 10,
        )
        self.publisher = self.create_publisher(Twist, 'cmd_vel', 10)
        self.timer = self.create_timer(0.1, self.tick)

    def on_pose(self, message):
        self.latest_pose = message

    def tick(self):
        command = Twist()
        command.linear.x, command.angular.z = choose_command(self.latest_pose)
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
