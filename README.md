# ПР04. Параметры ноды patrol

Локальная ветка `pr04` создана от личной `pr03`: преподавательская ветка
`pr04` в GitVerse пока отсутствует. В этой работе нода `patrol` получила
изменяемые параметры скорости и частоты публикации. Реализация и проверка
описаны в [parameters.md](evidence/pr04/parameters.md); сырые результаты
сохранены в [tests.txt](evidence/pr04/tests.txt) и
[defect.txt](evidence/pr04/defect.txt). Push ветки не выполнялся.

## Код и проверка

- [Нода](src/patrol/patrol/patrol.py): параметры, проверка до применения,
  пересоздание единственного таймера при допустимой смене `publish_hz`.
- [Чистая функция](src/patrol/patrol/control.py) и
  [тесты](src/patrol/test/test_parameters.py): диапазоны, нечисловые и
  неконечные значения, атомарность отклонённого обновления.
- [Живой сценарий](scripts/check_pr04.py) проверяет работающий turtlesim,
  переход 10→5 Гц, отклонение 0 и −1, сервис `/clear` и обнаружение действия
  `/turtle1/rotate_absolute`.
- [Отчёт](evidence/pr04/report.json),
  [GitHub Actions](.github/workflows/pr04.yml) и
  [декларация использования ИИ](AI_USAGE.md).

Проверенная среда: ROS 2 Lyrical, закреплённый Docker-образ курса. В
терминале контейнера с репозиторием в `/work`:

```bash
cd /work
source /opt/ros/lyrical/setup.bash
export ROS_DOMAIN_ID=48
export ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST
export QT_QPA_PLATFORM=offscreen
colcon build --symlink-install --packages-select turtle_bringup patrol
source install/setup.bash
python3 -m pytest -q src/patrol/test scripts/test_check_pr03.py
python3 scripts/check_pr04.py
```

Живой сценарий использует настоящий turtlesim без окна и требует свободного
ROS-домена. Отдельно проверить параметры вручную можно через
`ros2 launch turtle_bringup sim.launch.py` и
`ros2 run patrol patrol --ros-args -r cmd_vel:=/turtle1/cmd_vel` в двух
терминалах с теми же переменными окружения и подключённым workspace.
Команды `ros2 param set /patrol publish_hz 5.0` и
`ros2 param set /patrol publish_hz 0.0` показывают принятие допустимого
значения и отказ для нуля. Замер: `ros2 topic hz /turtle1/cmd_vel`.

Результат локального прогона: сборка двух пакетов, **22 passed** в pytest,
живой поток 9,998→4,999 Гц, сохранение 5 Гц после отказа в нуле и −1.
При временно отключённой проверке ноль воспроизвёл `ZeroDivisionError`;
проверка восстановлена. Команды и полный вывод находятся в evidence.

Публичный checker из course kit `v1-w07` запускается локально:

```bash
python3 .course-kit/pr04/v1/tools/check_practice.py PR04 --submission . --json
```

Checker сопоставляет коммит реализации с SHA в `evidence/pr04/report.json`:
после него могут меняться только evidence ПР04 и `AI_USAGE.md`.
GitHub Actions не запускался, поскольку ветка не публиковалась.

## ПР03: первая нода, поза и команда

Ветка `pr03` продолжает `pr02`: пакет `turtle_bringup` сохранён, рядом добавлен
`patrol`. Ветки `pr01`, `pr02` и `master` содержат прежние работы.
Исторические evidence ПР01/ПР02 сохранены; их отчёты проверяются на соответствующих
ветках. Здесь CI проверяет ПР03. Обязательная часть выполнена без
необязательного маршрута мышью. Исходная ветка GitVerse уже содержала
реализацию и демонстрационный отчёт; результаты повторной проверки сохранены
в `evidence/pr03/`.

## Что читать

- [Нода](src/patrol/patrol/patrol.py) — подписка, состояние и таймер.
- [Чистая функция](src/patrol/patrol/control.py) и [тесты](src/patrol/test/test_patrol.py).
- [Опыт, команды и объяснение](evidence/pr03/demo.md), [сырой вывод проверок](evidence/pr03/tests.txt), [отчёт](evidence/pr03/report.json).
- [CI для личного GitHub](.github/workflows/pr03.yml), [исходный workflow GitVerse](.gitverse/workflows/pr03.yml), [помощь ИИ](AI_USAGE.md).

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
python3 -m pytest -q src/patrol/test scripts/test_check_pr03.py
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
Каждый диагностический CLI-запрос ждёт нужный тип и количество endpoints
не более 20 секунд: новый участник DDS может ещё не видеть работающие ноды.
Повторяются только отсутствие объекта и неполный граф; остальные ошибки CLI
сразу прерывают проверку. В логе видны номер попытки, код возврата и оба потока.
Никакие файлы в evidence скрипт сам не переписывает: результат выводится в stdout.

Чистые тесты и ROS-тесты запускаются явным pytest, чтобы успешный `colcon test`
без обнаруженных тестов не считался доказательством. Исходная сборка и этот
сценарий включены в GitHub Actions для ветки `pr03`; Node.js в ROS-образе
нужен для работы checkout. Исходный workflow GitVerse сохранён.

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

## Отчёт и публикация

Локальная сборка, тесты и опыт с turtlesim выполнены 5 октября 2026 года;
результаты находятся в `evidence/pr03/tests.txt` и `demo.md`. Ветка GitVerse
уже содержала демонстрационную реализацию. Метаданные `patrol` приведены к
личному GitHub; добавлен workflow GitHub Actions.

Порядок сдачи: коммит реализации фиксирует пакет, README и workflow. Его полный
SHA указывается в `evidence/pr03/report.json`. Следующий коммит содержит
подтверждающие материалы и `AI_USAGE.md`. После push ветки `pr03` в личный
GitHub требуется успешный run для коммита evidence. Удалённый run локальной
проверкой не заменяется.
