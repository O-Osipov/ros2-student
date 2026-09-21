# ПР02. Терминал, пакет и запуск turtlesim

Демонстрационное выполнение задания студентом: пустой `ament_python`-пакет,
установленный launch-файл, управление через CLI и диагностика неверного топика.
Своей ноды и готового решения ПР03 здесь нет.

## Ветки и результаты

- `pr01` — завершённая первая работа; `master` сохраняет тот же исходный снимок.
- `pr02` — продолжение ПР01 с выполненной второй работой.
- [Команды, наблюдения и объяснение сбоя](evidence/pr02/commands.md).
- [Типы сообщений](evidence/pr02/types.md), [отчёт](evidence/pr02/report.json).
- [Декларация помощи ИИ](AI_USAGE.md), [CI ПР02](.gitverse/workflows/pr02.yml).
- [Описание прежнего опыта ПР01](PR01.md) и `evidence/pr01/` сохранены для истории.
  ПР01 проверяется на ветке `pr01`; её старый report.commit не описывает код ПР02.
  Workflow ПР01 находится в ветке `pr01`, здесь его заменяет workflow ПР02.

## Среда

Ubuntu 26.04, ROS 2 Lyrical, домен 46. Использован закреплённый образ:

```text
osrf/ros:lyrical-desktop-full@sha256:e6b1cb530b65588279681db53784e264ce5cf83f2cc33e689d27d6024d7f3ebe
```

Опыт выполнен настоящим `turtlesim_node` с `QT_QPA_PLATFORM=offscreen`:
окно не выводилось, движение доказано координатами Pose и состоянием графа.
Для демонстрации окна запускайте те же команды в своей графической ROS-среде
без `QT_QPA_PLATFORM=offscreen`; настройка X11-контейнера описана в [ПР01](PR01.md).
Не запускайте одновременно старый turtlesim или teleop. Во всех терминалах
используйте один выделенный вам домен.

## Сборка и запуск

Из корня workspace в свежем терминале:

```bash
source /opt/ros/lyrical/setup.bash
export ROS_DOMAIN_ID=46
set -o pipefail
colcon build --symlink-install --packages-select turtle_bringup
source install/setup.bash
ros2 pkg prefix turtle_bringup
test -f "$(ros2 pkg prefix turtle_bringup)/share/turtle_bringup/launch/sim.launch.py"
ros2 launch turtle_bringup sim.launch.py
```

Пакет уже создан. Не запускайте `ros2 pkg create` поверх имеющихся файлов.
[build-empty.txt](evidence/pr02/build-empty.txt) получен до добавления launch,
[build.txt](evidence/pr02/build.txt) — после. В `setup.py` launch установлен
через `data_files`, а маркер индекса и `package.xml` сохранены.
В другом терминале проверьте граф, затем остановите launch через Ctrl+C:

```bash
source /opt/ros/lyrical/setup.bash
export ROS_DOMAIN_ID=46
ros2 node list --no-daemon --spin-time 2
```

Нода `/turtlesim` исчезает. Повторно запустите launch для опыта ниже.

## Эксперимент

В терминале B подключите ROS и домен 46, получите позу и отправьте команду:

```bash
ros2 topic echo /turtle1/pose --once
ros2 topic pub --once /turtle1/cmd_vel geometry_msgs/msg/Twist \
  '{linear: {x: 1.0}, angular: {z: 0.5}}'
ros2 topic echo /turtle1/pose --once
```

Дождитесь остановки черепахи. Затем в B публикуйте ту же команду в неверное имя:

```bash
ros2 topic pub --rate 1 --wait-matching-subscriptions 0 \
  /cmd_vel geometry_msgs/msg/Twist \
  '{linear: {x: 1.0}, angular: {z: 0.5}}'
```

В C (та же ROS и домен) выполните:

```bash
ros2 topic info /cmd_vel --verbose
ros2 topic info /turtle1/cmd_vel --verbose
ros2 topic echo /turtle1/pose --once
```

У `/cmd_vel` один издатель и нет подписчика. У `/turtle1/cmd_vel` есть
подписчик, но нет издателя. Черепаха не движется. Остановите B через Ctrl+C,
измените **только имя** на `/turtle1/cmd_vel` и повторите. Теперь у топика
один издатель и один подписчик; поза меняется. Остановите издателя и launch.
Все исходные выводы и сравнение сохранены в `evidence/pr02/`.

## Проверка исходников и отчёта

```bash
source /opt/ros/lyrical/setup.bash
python3 -m py_compile src/turtle_bringup/launch/sim.launch.py
(cd src/turtle_bringup && python3 -m pytest test -q)
curl -fsSLo course-kit.tar.gz \
  https://ros.lms.ci.nsu.ru/downloads/robotics-course-kit-v1-w02-5d210c431e32.tar.gz
printf '%s  %s\n' \
  5d210c431e32418f45e2cffa9dd2028116c7a9520a36f3c7079c778cd73437a8 \
  course-kit.tar.gz | sha256sum -c -
mkdir -p .course-kit/pr02
tar -xzf course-kit.tar.gz -C .course-kit/pr02
python3 .course-kit/pr02/v1/tools/check_practice.py PR02 --submission .
```

Сгенерированные линтеры запускаются из каталога пакета: из корня workspace
они захватывают также копии в build/install. Проверка copyright по умолчанию
пропущена генератором ROS; это явно видно в `package-tests.txt`.
CI собирает пакет, проверяет установку launch и отчёт; GUI в CI не запускается.
Локальные проверки не являются ссылкой на успешный run GitVerse.

В закреплённом ROS-образе нет `node`. GitVerse использует его для JavaScript
действия `actions/checkout@v4`, включая завершающий шаг `post`, который удаляет
учётные данные. Поэтому **до checkout** workflow запускает обычный shell-шаг:
под root устанавливает `nodejs` из Ubuntu 26.04 и проверяет версию ≥ 20.
Локально проверена версия 22.22.1. `actions/setup-node` до bootstrap не поможет:
это тоже JavaScript action. Node остаётся в контейнере до завершения job.

На облачном раннере GitVerse
[нет доступа к docker.sock](https://gitverse.ru/docs/cicd/docs/runners/cloud-hosted/),
поэтому здесь ROS работает в `jobs.practice.container`, а не через `docker run`
из шага. Для старого образа Jazzy этот способ установки Node нельзя переносить
без проверки версии пакета Ubuntu.

Первый удалённый run выявил отсутствие `node`. Прежний локальный лог
`ci-local.txt` проверял только shell-шаги и этого не обнаружил. Проверка после
исправления отдельно выполняет настоящий checkout main и post с локальным
источником Git и тестовым токеном; описание и новые логи находятся в
[evidence/pr02/ci-runtime.md](evidence/pr02/ci-runtime.md).
Новый удалённый run ещё должен пройти после push владельцем.

## Два коммита и сдача

Коммит A содержит пакет, README и workflow. Коммит B содержит только
`evidence/pr02/` и обновление `AI_USAGE.md`. `report.commit` равен SHA **A**,
а сдаётся полный SHA **B** вместе со ссылкой на успешный run именно для B.
После изменения исходников нужно сделать новый A и обновить evidence.

```bash
git log -2 --oneline
python3 -c 'import json; print(json.load(open("evidence/pr02/report.json"))["commit"])'
git rev-parse HEAD
```

Публикация подготовленных веток владельцем репозитория:

```bash
git push -u origin pr01
git push -u origin pr02
```

После push откройте вкладку CI/CD GitVerse. До завершения удалённого run
репозиторий служит локально проверенным примером, а не готовой ссылкой на сдачу.
