# ПР06: дерево систем координат

Источником размеров служит `models/course_ackermann/model.sdf` из проверенного
course kit `v1-w09`. Xacro сохраняет СИ и оси REP-103: x вперёд, y влево,
z вверх. Корень дерева — `base_link`. В обязательной части все сочленения
фиксированные, поэтому `joint_state_publisher` не требуется.

| Родитель | Дочерний frame | xyz, м | Владелец преобразования |
| --- | --- | --- | --- |
| `base_link` | `camera_link` | `0.28 0 0.38` | единственный `robot_state_publisher` |
| `base_link` | `lidar_link` | `0.28 0 0.38` | единственный `robot_state_publisher` |
| `base_link` | `imu_link` | `0.28 0 0.38` | единственный `robot_state_publisher` |
| `base_link` | `front_left_wheel_link` | `0.40 0.31 0` | единственный `robot_state_publisher` |
| `base_link` | `front_right_wheel_link` | `0.40 -0.31 0` | единственный `robot_state_publisher` |
| `base_link` | `rear_left_wheel_link` | `-0.40 0.31 0` | единственный `robot_state_publisher` |
| `base_link` | `rear_right_wheel_link` | `-0.40 -0.31 0` | единственный `robot_state_publisher` |

Поворот всех joints равен нулю; ориентация цилиндров колёс задана только
в их `visual` и `collision`. Семь рёбер соединяют восемь звеньев без цикла.
`check_urdf`, тест и `view_frames` подтвердили это дерево. `tf2_echo
base_link lidar_link` показал `(0.280, 0.000, 0.380)`.

Для опыта временно заменён родитель `lidar_link` на `camera_link` при том же
offset. Развёрнутый URDF по-прежнему проходил `check_urdf`, но тест
`test_tree_and_sensor_placement` упал: ожидается `base_link`. Положение
лидара относительно базы стало бы `(0.56, 0, 0.76)` вместо
`(0.28, 0, 0.38)`. Строка восстановлена без коммита; повторный тест прошёл.
Исходный вывод — [defect.txt](defect.txt), итог —
[model-check.txt](model-check.txt).

`/tf_static` публикуется `robot_state_publisher` один раз с `RELIABLE` и
`TRANSIENT_LOCAL`; поздний подписчик с тем же durability получил все семь
преобразований (код 0), а `VOLATILE` не получил историческое сообщение
за 4 секунды (код 124). Полный вывод — [tf-qos.txt](tf-qos.txt).
Динамический `/tf` предназначен для меняющихся преобразований и имеет
`VOLATILE`; в этой модели динамических joints нет.

RViz с `QT_QPA_PLATFORM=offscreen` не мог создать окно GLX. При запуске
через доступный X-сокет с `QT_QPA_PLATFORM=xcb` и программным OpenGL
RViz и `robot_state_publisher` запустились и штатно завершились по SIGINT.
RViz сообщил о недоступных иконках курсора; визуальную корректность
отображения модели по одному логу подтвердить нельзя. Логи:
[rviz.txt](rviz.txt) и [rviz-xcb.txt](rviz-xcb.txt).

Реализация и evidence оформлены отдельными локальными коммитами. Требование
условия об отдельном коммите дефекта не выполнено: во время опыта коммиты
были запрещены, поэтому использованы временная обратимая правка и её лог.
Push не выполнялся.
