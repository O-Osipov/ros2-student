# ПР07 — Gazebo и мост

Пакет продолжает `course_description` из ПР06. Сборка и запуск выполняются
в Ubuntu 26.04 / ROS 2 Lyrical / Gazebo Jetty. Модель и мир скопированы из
course kit `v1-w10` (SHA-256 архива
`7a91d388d7bd3def7e058c8da48c32ff27ea6f14dc880a2da169c4102d456874`).
Изменения к исходным файлам: камера 15 Гц вместо 20 Гц; мост передаёт
исходную одометрию в `/vehicle/odom_gz` и публикует три сенсора с
`SENSOR_DATA` QoS.

```bash
source /opt/ros/lyrical/setup.bash
colcon build --symlink-install --packages-up-to course_simulation
source install/setup.bash
ros2 launch course_simulation simulation.launch.py headless:=true
```

`simulation.launch.py` сам добавляет установленный каталог моделей в
`GZ_SIM_RESOURCE_PATH`. Он запускает один сервер Gazebo, один мост,
`robot_state_publisher`, адаптер `/drive/safe` → `/vehicle/gz_cmd_vel`
и адаптер `/vehicle/odom_gz` → `/vehicle/odom` + `odom→base_link`.
Имена нод находятся в namespace `simulation`; контрактные топики абсолютные.
Мир уже включает одного `course_ackermann`, отдельный spawn не нужен.

В другом терминале можно послать безопасную тестовую команду со свежей меткой
времени симуляции:

```bash
source install/setup.bash
ros2 run course_simulation command_probe --speed 0.4 --steering 0.2 --seconds 4
```

Источник по окончании посылает нулевую команду. Узел привода также выдаёт
нулевой `Twist` при просроченной или нечисловой команде. Проверки данных
и последовательность воспроизведения дефекта описаны в `evidence/pr07`.

## Проверка и запись

```bash
source install/setup.bash
colcon test --packages-select course_simulation
colcon test-result --verbose
python3 scripts/check_pr07_runtime.py --seconds 15 > evidence/pr07/sensors.json
python3 scripts/record_pr07.py --sim-seconds 35
ros2 bag info fixtures/pr07-sensors > evidence/pr07/bag-info.txt
```

`record_pr07.py` не перезаписывает существующий каталог записи. Он завершает
recorder после 35 секунд по `/clock`, поэтому длительность самого MCAP
проверяется отдельно через `bag info`. Запись исключена из Git и остаётся
локальным входом ПР08. Для `/tf_static` recorder запрашивает `transient_local`
через `config/bag-qos.yaml`.

Намеренно неверная конфигурация и наблюдения до/после исправления находятся
в `evidence/pr07/defect.md`. Установленный `ros_gz_bridge` иногда выходит
с кодом `-11` при Ctrl+C; передача данных при работающем launch проверена
отдельно.
