# ПР02. Команды терминала, запуск и доставка Twist

Опыт выполнен **25 сентября 2026 года** в WSL2 и контейнере `pr01-student-demo` с ROS 2 Lyrical, `ROS_DOMAIN_ID=16`. Корень репозитория — `/home/user/work/ros2-pr01` на WSL-хосте и `/work` внутри контейнера. Пакет из [`src/turtle_bringup/`](../../src/turtle_bringup/) содержит исходные файлы, а установленный пакет после сборки найден в `/work/install/turtle_bringup`. Тест выполнялся с одним turtlesim и без teleop.

## Три использованные команды Linux

| Точная команда | Для чего | Фактический результат |
|---|---|---|
| `pwd` | Узнать текущий каталог перед созданием workspace | `/home/user/work/ros2-pr01` в WSL; [сырой вывод](linux.txt) |
| `ls -a` | Увидеть скрытые `.git`, `.github`, `.gitverse`, `.course-kit` и остальные элементы корня | Каталоги видны в [linux.txt](linux.txt) |
| `mkdir -p src evidence/pr02` | Создать каталог исходников и вложенный каталог свидетельств; `-p` допускает уже существующий `src` | Созданы `src/` и `evidence/pr02/`, подтверждены `ls -ld` в [linux.txt](linux.txt) |

`>` записывает stdout команды в файл, заменяя прежнее содержимое; `2>&1` направляет туда же stderr. `|` передаёт stdout следующей программе. В `colcon build ... 2>&1 | tee evidence/pr02/build.txt` вывод одновременно виден в терминале и записан на диск; `set -o pipefail` сохраняет код ошибки `colcon`, даже если `tee` завершился успешно. `source /opt/ros/lyrical/setup.bash` исполняет настройки в **текущем** Bash и меняет его окружение. Запуск файла как новой программы создал бы другой процесс и не установил бы эти переменные в родительском терминале. Точно так же `source install/setup.bash` добавляет собранный workspace в окружение текущего терминала.

## Пустой пакет и две сборки

Пакет создан внутри контейнера из `/work/src`:

```bash
ros2 pkg create --build-type ament_python --license Apache-2.0 \
  turtle_bringup --dependencies launch launch_ros turtlesim
```

В `package.xml` и `setup.py` записаны описание и GitHub noreply адрес сопровождающего. Сначала пакет не содержал launch-файла. Из корня `/work` с подключённой базовой ROS выполнено:

```bash
set -o pipefail
colcon build --symlink-install --packages-select turtle_bringup \
  2>&1 | tee evidence/pr02/build-empty.txt
```

[Первый лог](build-empty.txt): `1 package finished [2.97s]`. В отдельном процессе `source install/setup.bash; ros2 pkg prefix turtle_bringup` вернула `/work/install/turtle_bringup`. Это путь установленного **пакета**, а `pwd` — путь текущего каталога. После сборки нода не появилась: сборка и `source` не запускают ROS-процесс.

При первой попытке сборки `colcon` не смог записать в старый root-owned `log/`. Права **игнорируемого Git служебного** каталога были исправлены, затем сборка повторена с кодом 0; содержимое исходников из-за этого не менялось.

После добавления [`launch/sim.launch.py`](../../src/turtle_bringup/launch/sim.launch.py) и записи `glob('launch/*.launch.py')` в существующий `data_files` файла `setup.py` пакет пересобран той же командой. [Итоговый лог](build.txt): `1 package finished [2.54s]`. Проверка `ls "$(ros2 pkg prefix turtle_bringup)/share/turtle_bringup/launch"` показала установленный `sim.launch.py`; `python3 -m py_compile` прошла. Файл в `src/` сам по себе не был бы установленным ресурсом без `data_files`.

## Launch: запущенный процесс и остановка

В терминале A после `source /opt/ros/lyrical/setup.bash`, `source install/setup.bash`, `export ROS_DOMAIN_ID=16` выполнено:

```bash
ros2 launch turtle_bringup sim.launch.py
```

Launch запустил **готовый** `turtlesim_node` из установленного пакета `turtlesim`, а не Python-ноду `turtle_bringup`. [`ros2 node list --no-daemon --spin-time 5`](nodes-running.txt) показала `/turtlesim`. После Ctrl+C список стал [пустым](nodes-stopped.txt); затем launch запущен снова для опыта. [Вывод второго запуска и остановки](launch-experiment.txt) содержит `process started` и `process has finished cleanly`. После всех проверок Ctrl+C снова завершил launch, [итоговый список нод](nodes-final.txt) пуст. Наличие файла launch на диске, установленного ресурса и запущенной ноды — три разных состояния.

## Команда движения до сбоя

В терминале C `ros2 interface show geometry_msgs/msg/Twist` дал [поля `linear` и `angular`](twist-interface.txt), а `ros2 topic type /turtle1/pose` дал [`turtlesim_msgs/msg/Pose`](pose-type.txt). До публикации [поза](pose-before.txt): `x=5.544444561004639`, `y=5.544444561004639`, `theta=0`. Терминал B отправил:

```bash
ros2 topic pub --once /turtle1/cmd_vel geometry_msgs/msg/Twist \
  '{linear: {x: 1.0}, angular: {z: 0.5}}'
```

[Вывод издателя](publish-once.txt) показывает один Twist с `linear.x=1.0` и `angular.z=0.5`. Ожидалось движение вперёд с поворотом против часовой стрелки. [После команды](pose-working.txt) `x=6.509308815002441`, `y=5.796990871429443`, `theta=0.5040000081062317`: движение и поворот действительно произошли. Это одна публикация, поэтому нулевые скорости в снятой позже позе ожидаемы.

## Неверное имя и исправление

При работающем launch в B запущен непрерывный издатель **того же типа и с тем же значением**, но в `/cmd_vel`:

```bash
ros2 topic pub --rate 1 --wait-matching-subscriptions 0 \
  /cmd_vel geometry_msgs/msg/Twist \
  '{linear: {x: 1.0}, angular: {z: 0.5}}'
```

`--wait-matching-subscriptions 0` позволяет публиковать без подписчиков; [вывод](publish-broken.txt) подтверждает публикации. Пока он работал, `ros2 topic info /cmd_vel --verbose` показала [1 издателя, 0 подписчиков](topic-broken.txt). В то же время `ros2 topic info /turtle1/cmd_vel --verbose` показала [0 издателей, 1 подписчика turtlesim](topic-target-broken.txt). [Поза](pose-broken.txt) сохранила `x=6.509308815002441`, `y=5.796990871429443`, `theta=0.5040000081062317`. Издатель обнаружен в графе, но доставка до turtlesim не произошла.

Издатель остановлен через Ctrl+C и запущен той же командой, в которой заменено **только полное имя топика** на `/turtle1/cmd_vel`. Во время [публикации](publish-fixed.txt) `ros2 topic info /turtle1/cmd_vel --verbose` показала [1 издателя и 1 подписчика turtlesim](topic-fixed.txt). [Поза во время движения](pose-fixed.txt): `x=7.370705604553223`, `y=6.747246742248535`, `theta=1.156814694404602`, `linear_velocity=1.0`, `angular_velocity=0.5`. После Ctrl+C у издателя [скорости вновь нулевые](pose-resting.txt). Домен, тип сообщения, поля скорости и процесс симулятора не менялись.

| Наблюдение | До ошибки | `/cmd_vel`: ошибка | `/turtle1/cmd_vel`: исправлено |
|---|---|---|---|
| Издатель на целевом топике | Однократный CLI | 0 | 1 |
| Подписчик turtlesim на целевом топике | 1 | 1, но на другом топике | 1 |
| Получено движение | Да: x 5.544 → 6.509 | Нет: x остаётся 6.509 | Да: x 6.509 → 7.371 |

Причина — несовпадение **полного имени топика**. У `/cmd_vel` и `/turtle1/cmd_vel` одинаковый `geometry_msgs/msg/Twist`, но это разные потоки. Публикация и обнаружение CLI-издателя не означают, что у него есть подходящий подписчик. Совпадение типа необходимо, но недостаточно для доставки; ROS связывает конечные точки по имени топика и совместимым параметрам связи.
