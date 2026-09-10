# ПР01. Окружение и граф ROS 2

Результат работы с `turtlesim` в ROS 2 Lyrical: запуск готовых нод,
наблюдение графа, измерение частоты позы и опыт с `ROS_DOMAIN_ID`.

- [Граф, измерения и объяснение сбоя](evidence/pr01/graph.md)
- [Окружение](evidence/pr01/environment.json)
- [Отчёт ROS Doctor](evidence/pr01/doctor.txt)
- [Сводный отчёт для проверки](evidence/pr01/report.json)
- [Использование ИИ](AI_USAGE.md)
- [Workflow GitVerse](.gitverse/workflows/pr01.yml)

## Среда

Ubuntu 26.04, ROS 2 Lyrical, Gazebo Jetty 10.4.0. Все ноды запущены в одном
Docker-контейнере, графическое окно turtlesim выведено на Linux-хост через X11.
Дистрибутив и пакеты зафиксированы образом:

```text
osrf/ros:lyrical-desktop-full@sha256:e6b1cb530b65588279681db53784e264ce5cf83f2cc33e689d27d6024d7f3ebe
```

Команды ниже выполняются из корня репозитория. Для повторения использованного
GUI-запуска нужен Linux с рабочими `DISPLAY` и `XAUTHORITY`:

```bash
docker run -d --name pr01-student-demo --hostname pr01-demo \
  --network bridge \
  -e DISPLAY -e XAUTHORITY=/tmp/pr01.xauth -e ROS_DOMAIN_ID=16 \
  -v /tmp/.X11-unix:/tmp/.X11-unix:ro \
  -v "$XAUTHORITY:/tmp/pr01.xauth:ro" \
  -v "$PWD:/work" -w /work \
  osrf/ros:lyrical-desktop-full@sha256:e6b1cb530b65588279681db53784e264ce5cf83f2cc33e689d27d6024d7f3ebe \
  sleep infinity
```

Это команда для среды проведённого опыта. Для WSL2 и другой графической среды
настройка окна описана в [инструкции установки курса](https://ros.lms.ci.nsu.ru/course/installation).

В каждом из трёх терминалов A/B/C подключаюсь к **этому же** контейнеру:

```bash
docker exec -it pr01-student-demo bash
source /opt/ros/lyrical/setup.bash
export ROS_DOMAIN_ID=16
cd /work
```

## Исправный граф

В A запускаю симулятор:

```bash
ros2 run turtlesim turtlesim_node
```

В B запускаю управление и нажимаю стрелки, оставляя фокус в терминале B:

```bash
ros2 run turtlesim turtle_teleop_key
```

В C сохраняю сведения:

```bash
mkdir -p evidence/pr01
ros2 doctor --report > evidence/pr01/doctor.txt 2>&1
ros2 node list --no-daemon --spin-time 2 > evidence/pr01/nodes-before.txt
ros2 topic list -t > evidence/pr01/topics.txt
ros2 node info /turtlesim > evidence/pr01/turtlesim-info.txt
ros2 node info /teleop_turtle > evidence/pr01/teleop-info.txt
ros2 topic type /turtle1/pose > evidence/pr01/pose-type.txt
POSE_TYPE=$(cat evidence/pr01/pose-type.txt)
ros2 topic echo /turtle1/pose --once > evidence/pr01/pose-before.txt
```

Сначала измеряю частоту неподвижной черепахи. Таймер завершает замер сигналом
SIGINT, аналогично `Ctrl+C`; ненулевой код `timeout` здесь означает окончание
заданного интервала, а не отсутствие сообщений:

```bash
TIMEFORMAT='elapsed_seconds=%R'
{ time timeout --signal=INT 15s ros2 topic hz /turtle1/pose \
  > evidence/pr01/pose-hz.txt 2>&1; } 2> evidence/pr01/pose-hz-duration.txt
printf 'exit=%s\n' "$?" > evidence/pr01/pose-hz-exit.txt
```

После одного нажатия ↑ в B и остановки черепахи сохраняю новую позу в C:

```bash
ros2 topic echo /turtle1/pose --once > evidence/pr01/pose-after-key-working.txt
```

## Разрыв связи

A продолжает работать в домене 16. В B останавливаю teleop через `Ctrl+C`
и запускаю заново:

```bash
export ROS_DOMAIN_ID=17
ros2 run turtlesim turtle_teleop_key
```

В C выполняю проверку в домене 17. Переменная `POSE_TYPE` осталась после
исправного запуска и содержит `turtlesim_msgs/msg/Pose`:

```bash
export ROS_DOMAIN_ID=17
ros2 node list --no-daemon --spin-time 2 > evidence/pr01/nodes-broken.txt
timeout 5s ros2 topic echo /turtle1/pose "$POSE_TYPE" --once \
  > evidence/pr01/pose-broken.txt 2>&1
printf 'exit=%s\n' "$?" > evidence/pr01/pose-broken-exit.txt
```

Нажимаю ↑ в B. Для независимой проверки неподвижности один раз читаю позу
из домена симулятора. Префикс действует только на эту команду, текущий домен
C остаётся 17:

```bash
ROS_DOMAIN_ID=16 ros2 topic echo /turtle1/pose --once \
  > evidence/pr01/pose-after-key-broken-control.txt
```

## Восстановление

В B останавливаю teleop через `Ctrl+C` и возвращаю его в исходный домен:

```bash
export ROS_DOMAIN_ID=16
ros2 run turtlesim turtle_teleop_key
```

В C повторяю тот же тест доставки:

```bash
export ROS_DOMAIN_ID=16
ros2 node list --no-daemon --spin-time 2 > evidence/pr01/nodes-fixed.txt
timeout 5s ros2 topic echo /turtle1/pose "$POSE_TYPE" --once \
  > evidence/pr01/pose-fixed.txt 2>&1
printf 'exit=%s\n' "$?" > evidence/pr01/pose-fixed-exit.txt
```

Снова нажимаю ↑ в B, после остановки сохраняю результат в C:

```bash
ros2 topic echo /turtle1/pose --once > evidence/pr01/pose-after-key-fixed.txt
```

Значения, сравнение трёх состояний и причина сбоя находятся в
[graph.md](evidence/pr01/graph.md). Скриншоты сняты с окна turtlesim;
проверка доставки основана на выводе CLI и кодах завершения.

## Как составлен environment.json

В том же контейнере получены `/etc/os-release`, `uname -m`, `ROS_DISTRO`,
`ROS_DOMAIN_ID`, `gz sim --versions` и фактический RMW:

```bash
python3 -c 'from rclpy.utilities import get_rmw_implementation_identifier; print(get_rmw_implementation_identifier())'
```

Исходные значения сохранены в [environment-sources.txt](evidence/pr01/environment-sources.txt)
и перенесены в [environment.json](evidence/pr01/environment.json).
Digest совпадает с образом в команде `docker run`. JSON описывает ОС
контейнера и оба домена опыта; переменные X11 и полный набор переменных среды
в него не включены.

## Проверка отчёта

Из корня репозитория, уже на хосте с Python 3 и Git:

```bash
curl -fsSLo course-kit.tar.gz \
  https://ros.lms.ci.nsu.ru/downloads/robotics-course-kit-v1-w01-57866a9c98fa.tar.gz
printf '%s  %s\n' \
  57866a9c98fa3abdec27b35a180697ee680bfb0f05cc015970ce306d6d849fea \
  course-kit.tar.gz | sha256sum -c -
mkdir -p .course-kit
tar -xzf course-kit.tar.gz -C .course-kit
python3 -m json.tool evidence/pr01/environment.json > /dev/null
python3 .course-kit/v1/tools/check_practice.py PR01 --submission .
```

Комплект `v1-w01` зафиксирован по неизменяемому URL и SHA-256. Каталог
`.course-kit/` не входит в Git. Workflow GitVerse использует тот же архив,
проверяет JSON, совпадение digest и контракт evidence. Для ПР01 ROS в CI
не запускается: живой опыт выполнен локально.

В истории два коммита: первый содержит этот README и workflow, второй —
`evidence/pr01/` и `AI_USAGE.md`. Поле `report.commit` указывает на первый.
После push во вкладке **CI/CD** должен завершиться run второго коммита.
Ссылки на репозиторий, полный SHA этого коммита и успешный run составляют сдачу.
Проверка на GitVerse выполняется после публикации; локальный запуск тех же
команд CI записан в `evidence/pr01/ci-local.txt`.

После повторения опыта контейнер можно удалить с хоста:

```bash
docker rm -f pr01-student-demo
```
