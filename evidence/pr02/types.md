# Типы сообщений

| Топик | Тип в использованной Lyrical | Назначение |
|---|---|---|
| `/turtle1/cmd_vel` | `geometry_msgs/msg/Twist` | Команда движения; turtlesim подписывается |
| `/turtle1/pose` | `turtlesim_msgs/msg/Pose` | Текущее положение и скорости; turtlesim публикует |
| `/cmd_vel` | `geometry_msgs/msg/Twist` | Ошибочное имя в опыте; подписчика turtlesim нет |

Источники: `ros2 topic type /turtle1/pose` ([pose-type.txt](pose-type.txt)),
`ros2 topic info ... --verbose` ([topic-fixed.txt](topic-fixed.txt)),
`ros2 interface show geometry_msgs/msg/Twist` ([twist-interface.txt](twist-interface.txt)).
В Jazzy интерфейс позы называется `turtlesim/msg/Pose`.

`Twist` содержит два вектора: `linear` — линейная скорость, `angular` — угловая;
у каждого есть поля x/y/z. Для плоского turtlesim используем `linear.x`
(вперёд, условные единицы длины за секунду) и `angular.z` (рад/с, положительное
значение — против часовой стрелки). Остальные компоненты оставлены нулевыми.
В общем физическом ROS-интерфейсе линейная скорость задаётся в м/с.
`Twist` не содержит timestamp/frame_id и не задаёт целевую позицию.

`Pose`: x/y — координаты на плоскости симулятора, theta — угол в радианах,
linear_velocity/angular_velocity — текущие линейная и угловая скорости.
Изменение x/y/theta доказывает движение; нулевые скорости после прекращения
публикаций подтверждают остановку. Одной видимости топика для этого недостаточно.
