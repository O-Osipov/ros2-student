# ПР01. Окружение и граф ROS 2

Локальное выполнение ПР01 в WSL2 (Ubuntu 24.04) с ROS 2 Lyrical внутри Docker.
Результаты **повторного опыта 25 сентября 2026 года** находятся в
[evidence/pr01/](evidence/pr01/). Ранее опубликованный демонстрационный опыт
сохранён в истории Git; текущие evidence получены новым запуском.

- [Граф, измерение частоты и разрыв домена](evidence/pr01/graph.md)
- [Проверенное окружение](evidence/pr01/environment.json)
- [ROS Doctor](evidence/pr01/doctor.txt)
- [Сводный отчёт](evidence/pr01/report.json)
- [Декларация использования ИИ](AI_USAGE.md)
- [GitHub Actions](.github/workflows/pr01.yml)
- [GitVerse CI](.gitverse/workflows/pr01.yml)

## Среда и запуск

Использован образ
`osrf/ros:lyrical-desktop-full@sha256:e6b1cb530b65588279681db53784e264ce5cf83f2cc33e689d27d6024d7f3ebe`.
В контейнер смонтированы корень репозитория как `/work` и X11-сокет WSLg
`/tmp/.X11-unix`; `DISPLAY=:0`, `ROS_DOMAIN_ID=16`. Все три терминала опыта
работают **в одном контейнере**. Уже созданный контейнер запускается командой:

```bash
docker start pr01-student-demo
```

Для нового контейнера из корня клона в WSL2:

```bash
docker run -d --name pr01-student-demo --hostname pr01-demo \
  --network bridge -e DISPLAY="$DISPLAY" -e ROS_DOMAIN_ID=16 \
  -v /tmp/.X11-unix:/tmp/.X11-unix:rw \
  -v "$PWD:/work" -w /work \
  osrf/ros:lyrical-desktop-full@sha256:e6b1cb530b65588279681db53784e264ce5cf83f2cc33e689d27d6024d7f3ebe \
  sleep infinity
```

Откройте три WSL-терминала A, B, C. В каждом войдите в контейнер **с TTY** и
подключите ROS. Для teleop вариант без `-t` не работает: он не получает режим
клавиатурной консоли.

```bash
docker exec -it pr01-student-demo bash
source /opt/ros/lyrical/setup.bash
export ROS_DOMAIN_ID=16
cd /work
```

A запускает `ros2 run turtlesim turtlesim_node`, B запускает
`ros2 run turtlesim turtle_teleop_key`. В B нажмите ↑. В C проверьте граф:

```bash
ros2 doctor --report
ros2 node list --no-daemon --spin-time 5
ros2 topic list -t
ros2 node info /turtlesim
ros2 node info /teleop_turtle
ros2 topic type /turtle1/pose
ros2 topic echo /turtle1/pose --once
ros2 topic hz /turtle1/pose
```

Частота измеряется не меньше 10 секунд. В этом опыте `hz` работал 15 секунд
до SIGINT от `timeout`; длительность измерена монотонными часами на хосте.
Тип позы в Lyrical здесь — `turtlesim_msgs/msg/Pose`.

## Разрыв и восстановление связи

A остаётся в домене 16. Остановите teleop в B через Ctrl+C и запустите её
заново с `ROS_DOMAIN_ID=17`. В C также установите домен 17. Для сломанного
графа укажите тип позы явно, поскольку издатель из домена 16 не обнаруживается:

```bash
ros2 node list --no-daemon --spin-time 5
timeout 5s ros2 topic echo /turtle1/pose turtlesim_msgs/msg/Pose --once
```

Ожидается только `/teleop_turtle` и код таймаута 124 без сообщения Pose.
Клавиша ↑ в B не двигает черепаху; позу можно независимо прочитать из домена
симулятора через `ROS_DOMAIN_ID=16 ros2 topic echo /turtle1/pose --once`.

Затем остановите B и запустите teleop заново в домене 16. В C верните домен 16
и повторите **тот же** `timeout 5s ros2 topic echo`: теперь приходит Pose,
код выхода 0. После нового ↑ меняется координата x. Команды, первичные
выводы и причинное объяснение сохранены в [graph.md](evidence/pr01/graph.md).
По окончании остановите ROS-ноды через Ctrl+C и контейнер через
`docker stop pr01-student-demo`.

## Проверка и локальная сдача

Официальный course kit зафиксирован как `v1-w03` с SHA-256
`7fbfd3e8161ab6c6ebefc7663efdaf77d9a7d490399743507f33dcefbd5ac522`.
Архив получен по неизменяемому адресу
`https://ros.lms.ci.nsu.ru/downloads/robotics-course-kit-v1-w03-7fbfd3e8161a.tar.gz`,
проверен по SHA-256 и распакован в игнорируемый Git каталог `.course-kit/v1`.
Локальная проверка из корня репозитория:

```bash
python3 -m json.tool evidence/pr01/environment.json > /dev/null
python3 -m json.tool evidence/pr01/report.json > /dev/null
python3 .course-kit/v1/tools/check_practice.py PR01 --submission .
```

ПР01 не требует сборки своего ROS-пакета. CI проверяет JSON, digest архива и
состав evidence, включая связь отчёта с коммитом реализации; живое поведение
ROS подтверждается локальными логами и повторением опыта на защите.
`report.commit` указывает на коммит реализации **до** фиксации evidence.
Следующий коммит содержит результаты и `AI_USAGE.md`. GitHub Actions начнёт
работать только после отдельного push; локальные коммиты сами по себе не дают
ссылку на успешный CI run.
