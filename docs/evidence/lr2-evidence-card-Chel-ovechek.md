# Evidence card ЛР2: валидатор данных и тесты контракта

## 1. Идентификация

- ФИО: Псюрников Владимир
- Группа: Т.МО41
- Команда: 1
- GitHub: `Chel-ovechek`
- Роль: Quality engineer
- Контрольная точка: тег `lr2-v1`, коммит `322b0df3c14efefa600a6556d6fbcf07f5a4a4fc`

## 2. Собственный вклад

Issue: [#22](https://github.com/GundosCore/T26_MLOps/issues/22) (общая задача ЛР2).
PR: [#25](https://github.com/GundosCore/T26_MLOps/pull/25) (мой `main` → ветка `psyurnikov`), затем [#27](https://github.com/GundosCore/T26_MLOps/pull/27) (`psyurnikov` → `main`).
Номера строк ниже указаны для тега `lr2-v1`.

1. **Валидатор данных и тесты контракта.** Коммит [`ff481ac`](https://github.com/GundosCore/T26_MLOps/commit/ff481ac) «Add data validator and contract tests»: новые файлы `src/mlops_team1/validate_data.py` (+280 строк) и `tests/test_data_contract.py` (+171 строка). В валидаторе мои проверки обязательных и лишних столбцов, минимального числа строк, пропусков, типов, диапазонов, допустимых значений, дубликатов и порядка дат: `check_required_columns` (строки 154–158), `check_extra_columns` (160–166), `check_minimum_rows` (168–174), `check_not_null` (188–199), `check_types` (201–215), `check_ranges` (217–234), `check_allowed_values` (236–250), `check_duplicates` (252–267), `check_sorted` (269–287), сборка в `run_checks` (289–304). Код возврата: `0` для корректных данных, `1` при нарушении, `2` при ошибке чтения файла или контракта.
2. **Исправления по ревью.** Коммит [`6ec1b9b`](https://github.com/GundosCore/T26_MLOps/commit/6ec1b9b) «fix: check row length and strict date format» (+35/−2 строки):
   - новая проверка `check_row_length`, `validate_data.py` строки 176–185, подключена в `run_checks` на строке 296: лишняя или недостающая ячейка в строке CSV раньше проходила с кодом 0;
   - строгий формат даты в `parse_value`, строки 119–126: `strptime` принимал `2026-1-5`, теперь результат сравнивается с исходной строкой;
   - тесты в `tests/test_data_contract.py`: `extra_cell_in_row` и `date_without_leading_zero` (строки 134–143), `test_short_row_is_detected` (строки 152–157).
3. **Исправление предупреждения Ruff DTZ007.** Коммит [`92b2e43`](https://github.com/GundosCore/T26_MLOps/commit/92b2e43): в `parse_value` вместо `# noqa: DTZ007` дата разбирается через `.replace(tzinfo=UTC)` (строки 120–124), в строке 10 добавлен импорт `UTC`. Правило подавлено не было, а выполнено.

## 3. Проверка коллеги

Review PR [#24](https://github.com/GundosCore/T26_MLOps/pull/24) (контракт данных Станислава): [мой review](https://github.com/GundosCore/T26_MLOps/pull/24#pullrequestreview-5638697235).

Проверенный критерий: правила `data/contract.json` должны проверяться автоматически, а не только описываться. Для поля `FlightDate` в контракте задано `sorted: ascending`, поэтому нужны отдельная проверка порядка дат и негативный тест с неотсортированными датами. Это выполнено: `check_sorted` и тест `unsorted_dates` (`tests/test_data_contract.py`, строка 130). Также сверил обоснования диапазонов и описание целевой переменной `ArrDelay`.

## 4. Воспроизведение

```powershell
git fetch upstream --tags
git checkout lr2-v1
python -m pip install -e ".[dev]"
python -m ruff check .
python -m pytest -q
python -m mlops_team1.validate_data --data data/flights_sample.csv --contract data/contract.json --report reports/validation/lr2.json
```

- Версия контракта: `1.0.0`
- SHA-256 образца `data/flights_sample.csv`: `d2038bfd4ba28a304e1bed26578c9bfcb556942b51694b8342a75f4f2dbf617e`
- Результат: `All checks passed!`, `25 passed`, 10 проверок `OK`, код завершения `0`, в отчёте `passed: true`, `time_order_ok: true`.
- CI: [запуск для PR #25](https://github.com/GundosCore/T26_MLOps/actions/runs/40192720302/job/121166973805?pr=25).

Границы периодов (блок `split` отчёта):

| Часть      | Строк | Даты                    |
| ---------- | ----- | ----------------------- |
| train      | 14    | 2026-01-05 … 2026-01-18 |
| validation | 5     | 2026-01-19 … 2026-01-23 |
| test       | 5     | 2026-01-24 … 2026-01-28 |

Отчёт `reports/validation/lr2.json` в Git не попадает (`reports/` в `.gitignore`).

## 5. Отрицательный сценарий

Нарушение внесено во временную копию, эталонный файл не менялся: в строке за 2026-01-10 `DepHour` заменён с 10 на 25.

```powershell
(Get-Content data\flights_sample.csv) -replace '^2026-01-10,10,1,','2026-01-10,25,1,' | Set-Content $env:TEMP\bad.csv
python -m mlops_team1.validate_data --data $env:TEMP\bad.csv --contract data/contract.json --report $env:TEMP\bad.json
$LASTEXITCODE
```

```text
FAIL ranges: 1 violation(s): DepHour line 7: 25 not in [0, 23]
```

Остальные девять проверок `OK`, код завершения `1`, в отчёте `passed: false` и `split: null`: некорректные данные не разбиваются. Сработала проверка `ranges`.

## 6. Обоснование

- **Правило контракта.** `DepHour` — локальный час вылета, целое число от 0 до 23 (`data/contract.json`, строки 16–23). Значение 25 не существует, поэтому нарушение блокирует валидацию с кодом 1. Проверка работает до обучения, чтобы ошибка не дошла до модели.
- **Риск утечки.** Прогноз строится за 60 минут до планового вылета. `ArrDelay` становится известен только после прилёта, поэтому это источник цели (`ArrDelay >= 15`), а не признак. `DepHour` допустим только как плановый час: фактический час вылета уже содержит задержку. Разбиение строго по времени, без перемешивания, чтобы информация из будущего не попадала в train. Порядок дат проверяет `check_sorted`.
- **Ограничения.** Образец — 24 строки, по одному рейсу в день: он подходит для проверки контракта и воспроизводимости, но не для оценки качества модели на реальных рейсах. Нарушение порядка времени в блоке `split` (`time_order_ok: false`) пока не делает отчёт неуспешным; порядок дат в самом файле при этом блокируется проверкой `sorted`.

## 7. Использование ИИ

ChatGPT использовался для структурирования и редактирования текста карточки. Сам: написал валидатор и тесты, исправил замечания ревью (`6ec1b9b`, `92b2e43`), запускал `ruff`, `pytest` и валидатор, внёс нарушение `DepHour = 25` и получил код 1. Код валидатора и тесты могу объяснить по diff.
