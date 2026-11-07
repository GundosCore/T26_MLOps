# Evidence card ЛР3: версионирование данных и документация воспроизводимости

## 1. Идентификация

- ФИО: Псюрников Владимир Мелконович
- Группа: Т.МО41
- Команда: 1
- GitHub: `Chel-ovechek`
- Роль: Documentation reviewer (README, оговорки в документации, содержательное review PR этапа 1 и чужих PR, проверка карточек)
- Контрольная точка: коммит `b13cb1bc7c75e37052b6809831b93563c8b6063e` ветки `main`, на нём стоит командный тег `lr3-v1`

## 2. Собственный вклад

Issue: [#36](https://github.com/GundosCore/T26_MLOps/issues/36) (общая задача ЛР3), мой issue [#38](https://github.com/GundosCore/T26_MLOps/issues/38) (документация).
PR: [#39](https://github.com/GundosCore/T26_MLOps/pull/39) (мой `main` → ветка `psyurnikov`), слит. Review: Никита ([`snikersito`](https://github.com/snikersito)), одобрил.
Мои коммиты в PR: [`40ff70e`](https://github.com/GundosCore/T26_MLOps/commit/40ff70e855c3eca7358d337d14fc8a04760a84ec), `84e7adf`, `be034a3`, `f1846d2`; также мой служебный merge-коммит `316ffda` (подтянул `main`).
Часть правок по замечаниям ревью подготовил тимлид (Станислав), я прочитал diff и загрузил их; это указано в описании PR.

1. **README: разделы «Данные и DVC» и «Отклонения от задания (ЛР3)».** В «Данные и DVC» описано, почему данные не в Git, как получить текущую версию v2 и версию v1 через `dvc pull`, таблица идентификаторов версий (Git commit, DVC hash, SHA-256, размер), что не коммитить, предупреждение про CRLF (у v1 с CRLF было бы 507 байт вместо 482, это другой файл для DVC). В «Отклонения от задания» перечислены отличия от методички с причинами, в том числе v2 как синтетическое продолжение v1 с разрешения преподавателя.
2. **Оговорки в `docs/data-card.md`.** Пометка, что основной текст описывает v1; SHA-256 обеих версий в разделе 8; раздел 9 «Версия v2» (16 добавленных строк, seed 2026, 780 байт, DVC hash, отчёт `lr3-v2.json`). Описание v1 не переписывалось.
3. **Оговорки в `docs/leakage-and-split.md` (+30 −12).** Пометка про v1 и раздел «Границы для версии v2» с числами из `lr3-v2.json`: границы на позициях 24 и 32, разбиение 24/8/8. Test-период сдвинулся: бывший test v1 (2026-01-24…01-28) вошёл в train, потому что границы считаются по числу строк. Это не изменение test задним числом, файл v1 не менялся.

Остальные файлы в diff PR #39 (генератор v2, тесты, `v2-decision.md`, `lr3-v2.json`, `.dvc`) не мои: они попали из-за того, что ветка `psyurnikov` отставала от `main`. Моя работа: `README.md`, `docs/data-card.md`, `docs/leakage-and-split.md`.

## 3. Проверка коллег

Основное review: PR [#40](https://github.com/GundosCore/T26_MLOps/pull/40) (протокол воспроизводимости и тест отказа Екатерины): [мой review](https://github.com/GundosCore/T26_MLOps/pull/40#pullrequestreview-5787187603). Я проверял повторно после правок.

Что проверил: коммиты `f9f7e75` и `8df4aaa`, `tests/test_dvc_refusal.py`, `docs/reproducibility/lr3.md` целиком, вкладку Checks. Подтвердил закрытие замечаний: ruff красный из-за `subprocess.run` без `check`; тест искал слово `modified` в выводе `dvc status --quiet`, который ничего не печатает; `lr3.md` обрывался на незакрытом блоке кода. Сверил таблицу версий протокола (Git commit, md5, SHA-256, строки, размер) с PR #37, #43 и `.dvc`-файлом: совпало.

Другие мои review: [#37](https://github.com/GundosCore/T26_MLOps/pull/37#pullrequestreview-5736541004) (DVC, контракт 2.0.0 и v1: `.gitignore`, `.dvc/config` без секретов и абсолютных путей, md5 и размер v1) и [#43](https://github.com/GundosCore/T26_MLOps/pull/43#pullrequestreview-5771548847) (v2: причина, источник строк, период и влияние на границы в сообщении коммита, md5 и 780 байт, разбиение 24/8/8, нет данных и секретов в diff).

Найденная проблема: в PR #37 в описании осталась заглушка вместо ссылки на CI, а шаг CI по-прежнему писал отчёт под именем `lr2.json`. В PR #40 новых замечаний сверх трёх блокирующих я не нашёл, проверил их закрытие.

## 4. Воспроизведение

Выбранная версия: v2.

```powershell
git switch --detach c0224cb1b2537c5f1d0f952957adc20ac153acba
git rev-parse HEAD
dvc pull
Get-FileHash data\flights_sample.csv -Algorithm SHA256
python -m mlops_team1.validate_data --data data/flights_sample.csv --contract data/contract.json --report reports/validation/restored.json
$LASTEXITCODE
git switch main
dvc pull
```

| Версия | Git commit                                 | DVC hash (md5)                     | SHA-256 CSV                                                        | Строк | Контракт | Результат |
| ------ | ------------------------------------------ | ---------------------------------- | ------------------------------------------------------------------ | ----- | -------- | --------- |
| v1     | `a27bc82bb036f1cdb42153757e5abc217ecaa94c` | `b41ffd893842f7038a7004b9eb1e6628` | `d2038bfd4ba28a304e1bed26578c9bfcb556942b51694b8342a75f4f2dbf617e` | 24    | 2.0.0    | passed    |
| v2     | `c0224cb1b2537c5f1d0f952957adc20ac153acba` | `12e7b5a02885ff28f6560bd895a1330e` | `bf35cf01db04fb31de810dc16009d643e6bf3be22c791faea7c00fdbc25cff08` | 40    | 2.0.0    | passed    |

Мой вывод при восстановлении v2: `git rev-parse HEAD` напечатал `c0224cb1b2537c5f1d0f952957adc20ac153acba`; `dvc pull` сообщил `Everything is up to date.` (файл v2 уже был на месте); `Get-FileHash` дал `BF35CF01DB04FB31DE810DC16009D643E6BF3BE22C791FAEA7C00FDBC25CFF08`; валидатор напечатал 10 строк `OK` (`minimum_rows: rows=40, minimum=20`), код возврата 0. SHA-256 совпадает с протоколом: да.

## 5. Отказной сценарий

Рабочий CSV изменён вручную без `dvc add`:

```powershell
Add-Content data\flights_sample.csv "2026-02-14,10,1,0"
dvc status
dvc status --quiet; $LASTEXITCODE
dvc checkout --force
dvc status
```

`dvc status` показал `changed outs: modified: data\flights_sample.csv`. `dvc status --quiet` ничего не напечатал, код возврата 1. Хеш в `data/flights_sample.csv.dvc` остался старым, а файл другой, поэтому подмена видна сразу. После `dvc checkout --force` DVC вернул файл из cache (`M data\flights_sample.csv`), повторный `dvc status` сообщил `Data and pipelines are up to date.` Автоматическая версия проверки: `tests/test_dvc_refusal.py`.

## 6. Чем Git отличается от DVC cache и remote

- Git хранит код, конфигурацию и маленькие `.dvc`-файлы, где записан hash данных. Сам CSV в Git не лежит.
- DVC cache (`.dvc/cache`) это локальная папка с содержимым файлов на моей машине. В Git её нельзя: она большая и восстанавливается из remote.
- DVC remote (`course-local`, `../../dvc-storage`) это общее хранилище вне рабочего дерева. Данные уходят туда через `dvc push`, возвращаются через `dvc pull`.
- Три идентификатора: Git commit определяет проект, DVC hash объект данных, SHA-256 связывает конкретный файл с проверкой. Один не заменяет другой.

## 7. Использование ИИ

Использовал Claude: черновики текстов вставок в README, `data-card.md` и `leakage-and-split.md`, тексты ревью, описаний PR и структуру этой карточки. Сам: применял правки, прогонял ruff и pytest, читал diff PR #37, #40 и #43, сверял цифры с `.dvc`-файлами и отчётами, запускал восстановление и валидатор, проверял отказной сценарий.
Ошибка при работе с ИИ: Claude посоветовал отменить изменения в `docs/data-card.md` (Discard changes), хотя это были нужные правки; расхождение с содержимым файла выяснилось до отмены, совет был исправлен.
