# ПР05: запуск, несовместимость QoS и повтор MCAP

Опыт проведён 26 октября 2026 года в закреплённом ROS 2 Lyrical-образе
`osrf/ros@sha256:e6b1cb530b65588279681db53784e264ce5cf83f2cc33e689d27d6024d7f3ebe`.
Использованы `ROS_DOMAIN_ID=55`, `ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST`
и `QT_QPA_PLATFORM=offscreen`. Это настоящий turtlesim без видимого окна.
Ветка `pr05` создана от локальной `pr04`; преподавательской `pr05` нет.

## Система

`ros2 launch course_bringup patrol.launch.py` поднимает `/turtlesim`,
`/robot_a/patrol`, `/robot_a/pose_relay` и `/robot_a/pose_listener`.
Глобальная поза `/turtle1/pose` переназначена для двух namespaced нод;
выход `patrol` переназначен в `/turtle1/cmd_vel`. Это подтверждено
`ros2 node list` и `ros2 topic info --verbose` в сырых логах.
`pose_relay` предлагает `best_effort`, `volatile`, `keep_last(10)`.

## Сбой и причина

Первый запуск: `subscriber_reliability:=reliable record:=false`.
`/robot_a/sensor_pose` виден и имеет издателя, но надёжный подписчик
запрашивает более сильную гарантию, чем может предложить издатель.
`ros2 topic echo ... --qos-reliability reliable --once` завершился по
таймауту (код 124, сообщений нет). ROS сообщил `incompatible QoS` с
политикой `RELIABILITY`. Полный вывод — [qos-before.txt](qos-before.txt).
Отсутствие сообщений не связано с remap: `/turtle1/cmd_vel` имел одного
издателя `patrol` и одного подписчика `turtlesim`.
В выводе одного диагностического CLI-вызова есть предупреждение Fast DDS
о порте shared memory. Причина недоставки подтверждена отдельно профилями
конечных точек и предупреждением ROS `incompatible QoS: RELIABILITY`;
после смены профиля передача и replay работали в той же среде.

## Исправление, запись и replay

Второй запуск менял только аргумент на
`subscriber_reliability:=best_effort` и включал `record:=true`.
`pose_listener` получил сообщения, а CLI `echo --qos-reliability best_effort`
вернул Pose с кодом 0. `ros2 bag info` сообщил `Storage id: mcap`,
**один топик** `/robot_a/sensor_pose`, **416 сообщений** и один `.mcap` файл.
[bag-metadata.yaml](bag-metadata.yaml) скопирован из этого каталога.

После остановки живого launch тот же bag проигран с
`config/qos-overrides.yaml`, который задаёт `best_effort`, `keep_last(10)`.
При replay надёжный `echo` снова истёк по таймауту, а `best_effort` получил
Pose. Оба результата и `ros2 bag info` записаны в
[qos-after.txt](qos-after.txt). Bag-файл остался локально в
`evidence/pr05/bag-2/` и исключён из Git; доказательством сдачи служат
метаданные и сырые выводы.

Сборка трёх пакетов прошла; `colcon test-result --verbose` показал
24 теста, 0 ошибок, 0 провалов и 1 пропуск. [tests.txt](tests.txt)
сохраняет итоговую сводку. Отдельный pytest проверил
сценарий из ПР03. Повторяемый опыт находится в `scripts/check_pr05.py`.
Реализация сохранена отдельным локальным коммитом; его SHA указан в
`report.commit`. Evidence и декларация ИИ оформляются следующим коммитом.
Push ПР05 не выполнялся.
