# Исправление среды checkout — 2026-09-21

Исходный GitVerse run выявил `exec: node: not found` в завершающем шаге
checkout. Прежний `ci-local.txt` охватывал только `run` и не доказывал выполнение
JavaScript actions. Он и все исходные ROS-наблюдения сохранены без изменений.

Новый коммит реализации: `90b5f38e691b86f67f4e6eb18a6353fe802c8170`.
Изменены только `.gitverse/workflows/pr02.yml` и README. Дерево `src/` совпадает
с исходным `b5f51beef40d143572a264ee7f734e969f827afb`; ROS-опыт повторно не
проводился. Старые наблюдения относятся к тому же ROS-коду. Публичный checker
проверяет, что после нового `report.commit` меняются только evidence и AI_USAGE.

## Что проверено

- В свежем закреплённом Lyrical-образе `node --version` завершился с кодом 127.
- Первый shell-шаг workflow устанавливает Node под root до checkout. Из Ubuntu
  26.04 получена версия `v22.22.1` (nodejs `22.22.1+dfsg+~cs22.19.15-1ubuntu1`).
- Выполнен настоящий `dist/index.js` из `https://gitverse.ru/actions/checkout.git`,
  ref `v4`, commit `11d5960a326750d5838078e36cf38b85af677262`.
  Main получил нужный SHA и полную историю, затем post с состоянием main удалил
  тестовый auth header. Обе точки входа использовали один установленный Node.
- Между main и post выполнены все остальные shell-шаги workflow: сборка,
  установленный launch, тесты пакета, скачивание kit с проверкой SHA-256 и checker.

## Границы проверки

Это локальная проверка action и команд workflow, **не GitVerse runner**.
Git URL перенаправлен через `insteadOf` на локальный репозиторий; токен фиктивный.
Сеть/авторизация GitVerse, оркестрация и лимиты облачного runner этим не проверены.
До evidence-коммита только его ожидаемые файлы (`evidence/pr02/`, `AI_USAGE.md`)
наложены на чистый checkout коммита реализации. Такое незакоммиченное состояние
разрешает public checker; реализация при прогоне не изменяется.

Сырой вывод — `ci-runtime.txt`, воспроизводящий сценарий — `ci-probe.py`.
Для повторения нужны Docker, скачанный action указанного SHA и локальный repo:

```bash
docker run --rm --entrypoint python3 \
  -v "$PWD:/source:ro" \
  -v /path/to/checkout:/action:ro \
  osrf/ros:lyrical-desktop-full@sha256:e6b1cb530b65588279681db53784e264ce5cf83f2cc33e689d27d6024d7f3ebe \
  /source/evidence/pr02/ci-probe.py
```

Владелец отправляет ветку `pr02` и проверяет новый удалённый run до самого конца,
включая post checkout. Предыдущая ошибка не замалчивается и успешный удалённый
run до push не заявляется.

## Источники

- [Облачные раннеры GitVerse](https://gitverse.ru/docs/cicd/docs/runners/cloud-hosted/):
  docker.sock недоступен, поэтому остаётся job container, не вложенный docker run.
- [Checkout action GitVerse](https://gitverse.ru/actions/checkout): JavaScript
  main/post используют Node; post удаляет сохранённые учётные данные.
