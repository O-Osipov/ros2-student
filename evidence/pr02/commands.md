# Команды и наблюдения ПР02

## Условия опыта

21 сентября 2026 года; Ubuntu 26.04 / ROS 2 Lyrical, `ROS_DOMAIN_ID=46`.
Настоящий turtlesim работал с `QT_QPA_PLATFORM=offscreen`, без видимого окна.
В контейнер смонтирован репозиторий как `/work`, команды выполнялись от
пользователя хоста. Teleop не запускался. Среда подключена в каждом терминале:

```bash
source /opt/ros/lyrical/setup.bash
source /work/install/setup.bash  # после сборки
export ROS_DOMAIN_ID=46
```

## Linux на файлах этой работы

| Выполненная команда | Назначение | Наблюдение |
|---|---|---|
| `pwd` | Текущий каталог | `/work`, корень workspace |
| `printenv ROS_DISTRO ROS_DOMAIN_ID` | Только две настройки процесса | `lyrical`, `46` |
| `grep "Finished" evidence/pr02/build.txt` | Найти завершение пакета | строка `Finished <<< turtle_bringup` |

Исходный вывод этих команд, `ls -a` и `ros2 pkg prefix turtlesim`:
[linux.txt](linux.txt). `mkdir -p` использовался для создания каталогов.
`cd src` меняет рабочий каталог, а `ros2 pkg prefix` находит установленный пакет.

`>` записывает stdout в файл, заменяя его прежнее содержимое; `|` передаёт
stdout следующему процессу. `2>&1` направляет stderr туда же, куда stdout.
`tee` одновременно печатает поток и записывает его в файл. Например:

```bash
set -o pipefail
colcon build --symlink-install --packages-select turtle_bringup \
  2>&1 | tee evidence/pr02/build.txt
```

`pipefail` позволяет обнаружить ошибку сборки, даже если `tee` завершился успешно.
`source` выполняет файл в текущей оболочке и сохраняет изменения её окружения.
Запуск новой программы создаёт дочерний процесс: его изменения окружения
не возвращаются в родительский терминал. Ни сборка, ни source сами не запускают ноду.

## Пустой пакет → установленный launch

```bash
cd src
ros2 pkg create --build-type ament_python --license Apache-2.0 \
  turtle_bringup --dependencies launch launch_ros turtlesim \
  --description 'Launch turtlesim for practice PR02' \
  --maintainer-name 'Course demonstration' --maintainer-email student@example.com
cd ..
colcon build --symlink-install --packages-select turtle_bringup \
  2>&1 | tee evidence/pr02/build-empty.txt
```

[build-empty.txt](build-empty.txt) — успешная первоначальная сборка до добавления
launch. После source пакет находился, установленного `sim.launch.py` ещё не было.
Затем добавлены `launch/sim.launch.py` и запись установки в `setup.py`.
[build.txt](build.txt) — повторная сборка; [package-prefix.txt](package-prefix.txt)
указывает `/work/install/turtle_bringup`. Выполнены:

```bash
source install/setup.bash
test -f "$(ros2 pkg prefix turtle_bringup)/share/turtle_bringup/launch/sim.launch.py"
python3 -m py_compile src/turtle_bringup/launch/sim.launch.py
(cd src/turtle_bringup && python3 -m pytest test -q)
```

Проверки установки и синтаксиса завершились с кодом 0. В
[package-tests.txt](package-tests.txt) — 4 passed, 1 skipped: пропуск copyright
оставлен генератором ROS. Первый запуск pytest из корня workspace захватил
копии build/install и дал duplicate module; правильная рабочая директория —
каталог самого пакета, как в CI. Исходники ради обхода этой ошибки не менялись.

## Запуск и остановка

В A: `ros2 launch turtle_bringup sim.launch.py`.
В B: `ros2 node list --no-daemon --spin-time 2`.
В [nodes-running.txt](nodes-running.txt) есть `/turtlesim`.
После SIGINT группе launch (эквивалент Ctrl+C в терминале) launch завершился
с кодом 0; в [nodes-stopped.txt](nodes-stopped.txt) ноды нет.
Launch запущен повторно; [nodes-restarted.txt](nodes-restarted.txt) подтверждает граф.
[launch-first.txt](launch-first.txt) и [launch-experiment.txt](launch-experiment.txt)
содержат реальные журналы обоих запусков, включая завершение дочернего процесса.

## Правильное имя, сбой, исправление

Тип определён командой `ros2 topic type /turtle1/pose`. Поза снималась через
`ros2 topic echo /turtle1/pose turtlesim_msgs/msg/Pose --once`.
В B сначала отправлена одна команда:

```bash
ros2 topic pub --once /turtle1/cmd_vel geometry_msgs/msg/Twist \
  '{linear: {x: 1.0}, angular: {z: 0.5}}'
```

Ожидание: движение вперёд с поворотом против часовой стрелки. После прекращения
команд turtlesim останавливается. Затем запущен непрерывный неверный издатель:

```bash
ros2 topic pub --rate 1 --wait-matching-subscriptions 0 \
  /cmd_vel geometry_msgs/msg/Twist \
  '{linear: {x: 1.0}, angular: {z: 0.5}}'
```

В C проверены `ros2 topic info /cmd_vel --verbose` и
`ros2 topic info /turtle1/cmd_vel --verbose`. У неверного топика **1 издатель,
0 подписчиков**; у правильного — **0 издателей, 1 подписчик turtlesim**.
При первой проверке сразу после старта CLI ещё не обнаружил новый топик:
`Unknown topic`, exit=1. Повтор после discovery показал издателя; это ожидание
обнаружения, а не исправление имени. Команды и коды сохранены в [session.txt](session.txt).

После SIGINT неверному издателю исправлено только полное имя на
`/turtle1/cmd_vel`. Скорость, тип, частота публикации и домен сохранены.
Теперь [topic-fixed.txt](topic-fixed.txt) показывает **1 издатель и 1 подписчик**.

| Состояние | x | y | theta, рад |
|---|---:|---:|---:|
| До команды | 5.544445 | 5.544445 | 0.000000 |
| После одной правильной команды | 6.509309 | 5.796991 | 0.504000 |
| При публикации в /cmd_vel | 6.509309 | 5.796991 | 0.504000 |
| После исправления имени | 7.248984 | 6.511366 | 1.024000 |
| После остановки издателя | 7.533448 | 7.434896 | 1.512000 |

Вывод: неправильное имя не изменило координаты; правильное восстановило
движение. Совпадение типа `Twist` само по себе не соединяет разные топики.
Discovery позволяет увидеть издателя, но не означает наличие совместимого
подписчика у его имени. Это подтверждено endpoint counts и измерением Pose.

Первичные измерения: [pose-before.txt](pose-before.txt),
[pose-working.txt](pose-working.txt), [pose-broken.txt](pose-broken.txt),
[pose-fixed.txt](pose-fixed.txt), [pose-resting.txt](pose-resting.txt).
Последнее измерение получено после прекращения публикации и содержит нулевые
linear_velocity/angular_velocity. Поэтому его координаты отличаются от
измерения во время движения — черепаха ещё двигалась до таймаута команды.

После окончания launch остановлен; [nodes-final.txt](nodes-final.txt) пуст.
Числовые сравнения также сохранены в [observations.json](observations.json).
Это фактические результаты одного прогона, а не ожидаемые эталонные числа.

## Локальная проверка CI

В чистую копию коммита реализации A добавлены только текущие evidence и
AI_USAGE.md. В новом закреплённом контейнере последовательно выполнены все
`run`-шаги `.gitverse/workflows/pr02.yml`: сборка, проверка установки launch,
тесты каркаса, загрузка course kit, SHA-256 и публичный checker. Все завершились
успешно; [ci-local.txt](ci-local.txt) содержит фактический вывод. Сам сервис
GitVerse/checkout action локально не эмулировался; удалённый run ожидает push.
