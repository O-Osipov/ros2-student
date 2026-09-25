# ПР02. Пакет запуска turtlesim и адресация топика

Эта ветка продолжает исходную ветку `pr02` репозитория GitVerse. Собственная
ПР01 находится в [ветке pr01](https://github.com/O-Osipov/ros2-student/tree/pr01).
Ниже описано выполнение ПР02 в WSL2 и закреплённом Docker-образе.

ПР02 выполнена в той же среде WSL2 + Docker с ROS 2 Lyrical. Исходный пакет
[`src/turtle_bringup/`](src/turtle_bringup/) содержит `ament_python`-метаданные,
ресурсный маркер и [`launch/sim.launch.py`](src/turtle_bringup/launch/sim.launch.py).
Своей ROS-ноды в этой работе нет: launch запускает установленную ноду turtlesim.
[Команды и разбор опыта](evidence/pr02/commands.md) ·
[Типы сообщений](evidence/pr02/types.md) ·
[Отчёт](evidence/pr02/report.json).

Запустите ранее созданный контейнер `pr01-student-demo` и откройте в нём
терминал A. В каждом терминале опыта используйте одну установку и домен 16:

```bash
docker start pr01-student-demo
docker exec -it -u 1000:1000 -w /work pr01-student-demo bash
source /opt/ros/lyrical/setup.bash
export ROS_DOMAIN_ID=16
```

Из корня `/work` соберите пакет. В терминале запуска дополнительно подключите
`install/setup.bash`; сборку выполняйте в терминале с базовой ROS:

```bash
colcon build --symlink-install --packages-select turtle_bringup
source install/setup.bash
ros2 pkg prefix turtle_bringup
ls "$(ros2 pkg prefix turtle_bringup)/share/turtle_bringup/launch"
ros2 launch turtle_bringup sim.launch.py
```

После появления turtlesim в другом терминале проверьте `ros2 node list
--no-daemon --spin-time 5`. Остановка launch через Ctrl+C завершает симулятор.
Запустите launch снова для командного опыта. Убедитесь, что teleop и старые
экземпляры turtlesim остановлены. Для однократного движения:

```bash
ros2 topic pub --once /turtle1/cmd_vel geometry_msgs/msg/Twist \
  '{linear: {x: 1.0}, angular: {z: 0.5}}'
```

Сравните `/turtle1/pose` до и после. Для воспроизведения ошибки запустите
публикацию того же Twist в `/cmd_vel` с `--rate 1
--wait-matching-subscriptions 0`; `ros2 topic info /cmd_vel --verbose` покажет
`Subscription count: 0`. Остановите издатель через Ctrl+C и повторите его с
именем `/turtle1/cmd_vel`: теперь у топика есть подписчик turtlesim, поза
меняется. Полные команды и сырые выводы находятся в
[commands.md](evidence/pr02/commands.md). После опыта остановите launch и
контейнер.

CI для ПР02 — [GitHub Actions](.github/workflows/pr02.yml) и
[GitVerse](.gitverse/workflows/pr02.yml). Он собирает пакет в закреплённом
Lyrical-образе, проверяет установленный launch-файл, синтаксис Python и
контракт evidence по course kit `v1-w03` (SHA-256
`7fbfd3e8161ab6c6ebefc7663efdaf77d9a7d490399743507f33dcefbd5ac522`).
Локально:

```bash
python3 -m py_compile src/turtle_bringup/launch/sim.launch.py
python3 .course-kit/v1/tools/check_practice.py PR02 --submission .
```

`report.commit` указывает на коммит пакета, README и workflow. Следующий
коммит содержит только `evidence/pr02/` и запись ПР02 в `AI_USAGE.md`.
Для сдачи нужен успешный CI run на GitHub для текущего evidence-коммита ветки `pr02`.
