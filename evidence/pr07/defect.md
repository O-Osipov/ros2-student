# Опыт с неверным Gazebo-топиком IMU

1. Исправная конфигурация `src/course_simulation/config/bridge.yaml` скопирована
   в `evidence/pr07/bridge-bad.yaml`. Единственная намеренная разница —
   `gz_topic_name: /vehicle/imu_wrong` вместо `/vehicle/imu`.
   Точная разница сохранена в `defect-diff.txt`.
2. `simulation.launch.py` запущен с `bridge_config:=/work/evidence/pr07/bridge-bad.yaml`.
   Лог `headless-defect.txt` показывает **один** `parameter_bridge`,
   настроенный на `/vehicle/imu_wrong` → `/vehicle/imu`.
3. `imu-broken-ros-info.txt` показывает ROS publisher на `/vehicle/imu`.
   При этом `imu-broken-echo.txt` содержит timeout через 5 с без сообщения.
   На стороне Gazebo `imu-broken-gz-info.txt` показывает издателя исходного
   `/vehicle/imu`, а `imu-broken-gz-message.txt` содержит реальное IMU-сообщение.
   Одновременно `scan-working-echo.txt` подтверждает работающий лидар.
4. Ошибка лежит в имени Gazebo-топика, а не в SDF-сенсоре, QoS или общем
   отказе симуляции. Штатный YAML уже содержит правильное имя. После
   остановки ошибочного запуска запущен тот же launch с ним, без второго
   экземпляра моста. `headless-fixed.txt` показывает `/vehicle/imu` →
   `/vehicle/imu`; `imu-fixed-echo.txt` содержит сообщение с
   `frame_id: imu_link`; `imu-fixed-ros-info.txt` показывает одного издателя.

Отдельное наблюдение: при Ctrl+C `ros_gz_bridge` Jetty/Lyrical в двух запусках
завершился с кодом `-11` после успешной передачи данных. `drive_adapter`,
`odom_adapter`, Gazebo и `robot_state_publisher` в итоговом коротком запуске
остановились корректно. Этот сбой завершения не устранялся изменением
маршрута IMU и не используется как доказательство намеренного дефекта.
