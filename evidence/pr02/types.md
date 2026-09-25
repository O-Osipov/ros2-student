# ПР02. Типы топиков и поля сообщений

Типы проверены в ROS 2 Lyrical командами `ros2 interface show geometry_msgs/msg/Twist` и `ros2 topic type /turtle1/pose`. [Сырой интерфейс Twist](twist-interface.txt) · [тип позы](pose-type.txt).

| Полное имя топика | Тип | Назначение |
|---|---|---|
| `/turtle1/cmd_vel` | `geometry_msgs/msg/Twist` | Команда линейной и угловой скорости для turtlesim |
| `/turtle1/pose` | `turtlesim_msgs/msg/Pose` | Текущие x, y, угол и скорости черепахи |

`Twist.linear` и `Twist.angular` — два `geometry_msgs/msg/Vector3` с полями `x`, `y`, `z` типа `float64`. В выполненном опыте `linear.x=1.0` задавала движение вперёд, `angular.z=0.5` — поворот против часовой стрелки; остальные компоненты оставались нулевыми. Поза в Lyrical содержит `x`, `y`, `theta`, `linear_velocity` и `angular_velocity`; имя её типа взято из команды, а не перенесено из Jazzy.

Неверный `/cmd_vel` имел тот же тип `Twist`, но turtlesim подписывался на `/turtle1/cmd_vel`. [Данные об ошибочном топике](topic-broken.txt) и [исправленном](topic-fixed.txt) показывают разницу в числе подписчиков.
