# ПР03. Первая нода: поза и команда

Ветка `pr03` продолжает `pr02`: пакет `turtle_bringup` сохранён, рядом добавлен
`patrol`. Ветки `pr01`, `pr02` и `master` содержат прежние работы.
Исторические evidence ПР01/ПР02 сохранены; их отчёты проверяются на соответствующих
ветках. Здесь CI проверяет ПР03. Пример выполняет обязательную часть без маршрута мышью.

## Что читать

- [Нода](src/patrol/patrol/patrol.py) — подписка, состояние и таймер.
- [Чистая функция](src/patrol/patrol/control.py) и [тесты](src/patrol/test/test_patrol.py).
- [Опыт, команды и объяснение](evidence/pr03/demo.md), [сырой вывод проверок](evidence/pr03/tests.txt), [отчёт](evidence/pr03/report.json).
- [CI](.gitverse/workflows/pr03.yml), [помощь ИИ](AI_USAGE.md).

## Сборка и показ

Проверенная среда: ROS 2 Lyrical / Ubuntu 26.04, закреплённый контейнер из CI.
В каждом терминале подключите ROS, выберите свой домен (в этом примере 47)
и подключите workspace. Не запускайте одновременно старый patrol или teleop.

```bash
source /opt/ros/lyrical/setup.bash
export ROS_DOMAIN_ID=47
export ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST
colcon build --symlink-install --packages-select turtle_bringup patrol
source install/setup.bash
python3 -m pytest -q src/patrol/test
```

В терминале A: `ros2 launch turtle_bringup sim.launch.py`.
В B: `ros2 run patrol patrol`. В C:

```bash
ros2 node info /patrol
ros2 topic info /cmd_vel --verbose
ros2 topic info /turtle1/cmd_vel --verbose
```

У `/cmd_vel` один издатель и нет подписчиков: черепаха не движется.
Остановите B и измените только remap:

```bash
ros2 run patrol patrol --ros-args -r cmd_vel:=/turtle1/cmd_vel
```

В C: `ros2 topic hz /turtle1/cmd_vel`; измеряйте 10 секунд и остановите
измеритель Ctrl+C. Затем остановите B: после watchdog turtlesim движение
прекратится. Закройте A. Программа до первой Pose публикует нулевой Twist,
после — `(linear.x=0.5, angular.z=0.3)`. Контроль возраста Pose здесь не реализован.

## Автоматическое повторение

После сборки и source в том же терминале:

```bash
QT_QPA_PLATFORM=offscreen python3 scripts/check_pr03.py
```

Это настоящий ROS-опыт без видимого окна: проверяет нулевую команду до Pose,
разрыв имени, исправление только remap, частоту за 10 секунд, движение и
завершение по SIGINT. Наблюдатель временно подписывается на правильный cmd_vel,
поэтому во время измерения подписчиков больше, чем при ручном опыте.
Никакие файлы в evidence скрипт сам не переписывает: результат выводится в stdout.

Чистые тесты и ROS-тесты запускаются явным pytest, чтобы успешный `colcon test`
без обнаруженных тестов не считался доказательством. Исходная сборка и этот
сценарий также выполняются в GitVerse CI; Node.js там нужен для checkout/post.

## Проверка отчёта комплектом курса

```bash
curl -fsSLo course-kit.tar.gz \
  https://ros.lms.ci.nsu.ru/downloads/robotics-course-kit-v1-w03-7fbfd3e8161a.tar.gz
printf '%s  %s\n' \
  7fbfd3e8161ab6c6ebefc7663efdaf77d9a7d490399743507f33dcefbd5ac522 \
  course-kit.tar.gz | sha256sum -c -
mkdir -p .course-kit/pr03
tar -xzf course-kit.tar.gz -C .course-kit/pr03
python3 .course-kit/pr03/v1/tools/check_practice.py PR03 --submission .
```

Проверка отчёта дополняет тесты, но не доказывает работу ноды сама по себе.
Комплект, build/install/log и временные кэши не входят в Git.

## Отчёт и история

Сначала фиксируются код, тесты, README и workflow (коммит A). Затем реальные
результаты, report.json с SHA коммита A и запись PR03 в AI_USAGE.md (коммит B).
Сдаётся B со ссылкой на его CI. Локальный прогон не заменяет удалённый run:
push в GitVerse и проверку run выполняет владелец репозитория.

Предыдущая ПР02 подробно описана в `evidence/pr02/commands.md`, ПР01 — в `PR01.md`.
