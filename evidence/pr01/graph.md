# ПР01. Граф ROS 2 и разрыв связи между доменами

Дата опыта: **25 сентября 2026 года**. Хост — WSL2 Ubuntu 24.04; один Docker-контейнер `pr01-student-demo` с Ubuntu 26.04 и ROS 2 Lyrical. Все процессы ROS запускались внутри контейнера, а окно turtlesim использовало X11-сокет WSLg. Исходные выводы команд лежат рядом с этим файлом. [Окружение](environment.json) · [ROS Doctor](doctor.txt) · [Повторение опыта](../../README.md).

## Исправный граф

В контейнере запущены `turtlesim_node` и `turtle_teleop_key` с `ROS_DOMAIN_ID=16`. Teleop требовала интерактивного TTY (`docker exec -it`): первая попытка без `-t` завершилась ошибкой `Failed to get old console mode`, поэтому процессы для опыта перезапущены с TTY. Нажатия ↑ передавались в PTY teleop, команды движения публиковала сама ROS-нода.

`ros2 node list --no-daemon --spin-time 5` показала `/teleop_turtle` и `/turtlesim` ([вывод](nodes-before.txt)). `ros2 topic list -t` показала [пять топиков](topics.txt):

| Топик | Тип | Роль в опыте |
|---|---|---|
| `/turtle1/cmd_vel` | `geometry_msgs/msg/Twist` | `/teleop_turtle` публикует команды, `/turtlesim` подписывается |
| `/turtle1/pose` | `turtlesim_msgs/msg/Pose` | `/turtlesim` публикует позу; временные CLI-подписчики её читают |
| `/turtle1/color_sensor` | `turtlesim_msgs/msg/Color` | `/turtlesim` публикует цвет под черепахой |
| `/parameter_events` | `rcl_interfaces/msg/ParameterEvent` | События параметров |
| `/rosout` | `rcl_interfaces/msg/Log` | Логи ROS |

Связь издателя и подписчика `/turtle1/cmd_vel` сверена по [`ros2 node info /teleop_turtle`](teleop-info.txt) и [`ros2 node info /turtlesim`](turtlesim-info.txt). [`ros2 topic type /turtle1/pose`](pose-type.txt) отдельно подтвердила тип `turtlesim_msgs/msg/Pose`. CLI-подписчиков нет в исходном списке нод: список снят до выполнения `echo` и `hz`.

```text
клавиша ↑ → /teleop_turtle ── /turtle1/cmd_vel: Twist ──→ /turtlesim
                                                           │
                            ros2 topic echo/hz ←─ /turtle1/pose: Pose
```

Начальная [поза](pose-before.txt): `x=5.544444561004639`, `y=5.544444561004639`. После ↑ и остановки движения [x выросла](pose-after-key-working.txt) до `7.560444355010986`; y не изменилась. Это проверяет не только обнаружение нод, но и доставку команды.

## Частота публикации позы

`timeout --signal=INT 15s ros2 topic hz /turtle1/pose` работала [15,83 с по монотонным часам](pose-hz-duration.txt). В последней строке [сырого вывода](pose-hz.txt) указано `average rate: 63.284`, окно 812 измерений. Поза публиковалась и когда черепаха не двигалась. В выводе есть один отрицательный минимум интервала (`-0.146s`); поэтому значение 63,284 Гц следует считать показанием этого запуска `ros2 topic hz`, а не точной характеристикой таймера симулятора. [Код 124](pose-hz-exit.txt) здесь вызван заданным `timeout`, при этом сообщения реально поступали.

## Воспроизведение разрыва

Симулятор оставлен в домене 16. Teleop остановлена через Ctrl+C и запущена заново с `ROS_DOMAIN_ID=17`; наблюдение также выполнено из домена 17. [`node list`](nodes-broken.txt) показала только `/teleop_turtle`. Для чтения позы задан известный тип явно, поскольку в домене 17 издатель не обнаруживается:

```bash
timeout 5s ros2 topic echo /turtle1/pose turtlesim_msgs/msg/Pose --once
```

Команда завершилась с [кодом 124](pose-broken-exit.txt), её [stdout пуст](pose-broken.txt): сообщение Pose не получено. После ↑ в teleop из домена 17 дополнительный CLI-подписчик **в домене симулятора 16** прочитал прежнюю [позу](pose-after-key-broken-control.txt), `x=7.560444355010986`. Это контроль, что команда движения из другого домена не доставлена, а не успешное чтение в сломанном домене.

## Восстановление

Teleop остановлена и перезапущена с `ROS_DOMAIN_ID=16`; CLI-наблюдение также возвращено в 16. [`node list`](nodes-fixed.txt) снова показала обе ноды. **Та же команда** `timeout 5s ros2 topic echo` с тем же явным типом получила [Pose](pose-fixed.txt) и [код 0](pose-fixed-exit.txt). После нового ↑ [x выросла](pose-after-key-fixed.txt) с `7.560444355010986` до `9.576444625854492`.

| Проверка | До разрыва: A/B/C = 16/16/16 | Разрыв: 16/17/17 | После исправления: 16/16/16 |
|---|---|---|---|
| Ноды, видимые наблюдателю C | teleop и turtlesim | Только teleop | teleop и turtlesim |
| `echo` позы в C | Pose получена | Нет Pose, таймаут 124 | Pose получена, код 0 |
| x после ↑ | 7.560444 | 7.560444 | 9.576445 |

Причина: участники ROS с разными `ROS_DOMAIN_ID` в этой конфигурации не обнаруживают друг друга. Teleop в домене 17 не видит подписчика `/turtle1/cmd_vel` из домена 16, а CLI в домене 17 не видит издателя `/turtle1/pose`. Переменная окружения задаётся процессу при запуске: `export ROS_DOMAIN_ID=16` в оболочке не перенастраивает уже работающую ноду, поэтому teleop пришлось перезапустить. Симулятор и имена топиков в ходе разрыва не менялись.

Окно не использовалось как первичное доказательство: сравнение сделано по сохранённым выводам ROS CLI и кодам завершения. ROS-процессы после опыта остановлены через Ctrl+C, контейнер остановлен.
