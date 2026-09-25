# ПР02. Разбор первых запусков GitHub Actions

Первый пробный push ветки `pr02-lab` на коммите `6d62185596182f00e4d2065c3f7c7aa8048858d9` создал два красных запуска:

- [PR01, run 36106463030](https://github.com/O-Osipov/ros2-student/actions/runs/36106463030): шаг `check_practice.py PR01` завершился с кодом 1. В workflow ПР01 было `on: [push, pull_request]` для всех веток. Checker правильно сообщил, что после указанного в отчёте ПР01 коммита изменились README, CI и evidence следующей практики. Проверять контракт ПР01 на ветке ПР02 не требуется.
- [PR02, run 36106463012](https://github.com/O-Osipov/ros2-student/actions/runs/36106463012): установка Node и checkout прошли. Шаг сборки завершился до запуска `colcon`: `/opt/ros/lyrical/setup.bash: line 8: AMENT_TRACE_SETUP_FILES: unbound variable`. Причина — `set -u` перед `source` скрипта окружения ROS. Сборка не была причиной этого отказа.

В пробной ветке в коммите реализации `75901decccc93ce02359266d3704e1010ad34981` workflow ПР01 ограничен push ветки `pr01`, ПР02 — push ветки `pr02-lab`; настройки GitHub и GitVerse приведены к одному поведению. В шаге сборки ПР02 оставлены `-e` и `pipefail`, а `-u` снят перед `source` ROS. В чистом одноразовом контейнере из того же закреплённого образа после исправления прошли `colcon build --symlink-install --packages-select turtle_bringup`, `source install/setup.bash`, проверка установленного launch и `python3 -m py_compile` (`CI_BUILD_OK`). Живой ROS-опыт и его исходные логи остаются в [commands.md](commands.md).

Итоговый статус облачного run должен проверяться отдельно по SHA evidence-коммита после следующего push. Локальная сборка не подтверждает работу всего GitHub Actions job.

## Перенос в исходную ветку преподавателя

Исходная ветка `origin/pr02` сохранена как предок. Наши файлы реализации перенесены в коммит `4b5aea1c9886e2234a9be7fa54ab86190eef0f67`; затем перенесены реальные логи опыта из пробной ветки. Пакет снова собран в чистом закреплённом контейнере, установленный launch найден (`PR02_UPSTREAM_BUILD_OK`). Старые run выше относятся к пробной ветке; для сдачи нужен новый успешный run для итогового SHA ветки `pr02`.
