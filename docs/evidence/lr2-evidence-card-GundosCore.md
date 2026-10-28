# Evidence card ЛР2: контракт данных и защита от утечки

## 1. Идентификация

- ФИО: Соловцов Станислав Алексеевич
- Группа: Т.МО41
- Команда: 1
- GitHub: `GundosCore`
- Роль: Contract engineer; Repository administrator
- Контрольная точка: тег `lr2-v1`, коммит `322b0df3c14efefa600a6556d6fbcf07f5a4a4fc`

## 2. Собственный вклад

1. **Контракт данных v1.0.0.** PR #24 (ветка `lr2-contract`), в `main` попал
   коммитом `ac9c28c` («feat: add data contract v1.0.0 and document validation»).
   Новый файл `data/contract.json`, строки 1–40. Issue: #22 (общий issue ЛР2).
   - Поле `DepHour`: строки 16–23, диапазон 0–23.
   - Поле `ArrDelay`: строки 31–38, роль `target_source`, диапазон −180…1440.
2. **README и `.gitignore`** в том же PR #24. В README добавлен раздел «Данные и
   контракт (ЛР2)»: команда проверки, правило версий контракта (patch, minor,
   major) и решение не хранить отчёты в Git. В `.gitignore` добавлена строка
   `reports/`. Строки diff в `README.md`: 3 (описание проекта), 41 (ожидаемый
   результат проверок), 51–76 (новый раздел), 82–83 (структура репозитория);
   в `.gitignore`: строка 39 (`reports/`).
3. **Образец данных и правила игнорирования.** Коммит
   «chore: prepare sample dataset and gitignore» (PR #23):
   файл `data/flights_sample.csv` и исключения в `.gitignore`, которые пропускают
   в Git только контракт и образец.
4. **Слияния и приёмка.** Слил в `main` работу Владимира (PR #27, ветка
   `psyurnikov`) и Никиты (PR #30, ветка `skvortsov`); перед тегом выполнил
   приёмку в чистом клоне: `ruff`, `pytest`, валидатор, проверка SHA-256 образца.

## 3. Проверка коллеги

Review PR #25 (Владимир Псюрников, Quality engineer):
https://github.com/GundosCore/T26_MLOps/pull/25#pullrequestreview-5642982552

Найденные проблемы, которых не видели тесты и CI:

- Строка CSV с лишней ячейкой (`2026-01-05,5,0,4,99`) проходила проверку с кодом
  0: `csv.DictReader` складывает лишние значения под ключ `None`, и ни одна
  проверка их не читала.
- Дата `2026-1-5` принималась при формате `YYYY-MM-DD`, потому что `strptime`
  не требует ведущий ноль.

Исправлено автором в коммите `6ec1b9b`: проверка `row_length`, строгий разбор даты
и тесты `extra_cell_in_row`, `date_without_leading_zero`,
`test_short_row_is_detected`.

## 4. Воспроизведение

Чистый клон на теге:

```powershell
git clone --branch lr2-v1 https://github.com/GundosCore/T26_MLOps.git accept
cd accept
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
python -m ruff check .
python -m pytest -q
python -m mlops_team1.validate_data --data data/flights_sample.csv --contract data/contract.json --report reports/validation/lr2.json
```

- Версия контракта: `1.0.0`
- SHA-256 образца: `d2038bfd4ba28a304e1bed26578c9bfcb556942b51694b8342a75f4f2dbf617e`
- Результат: `All checks passed!`, 25 passed, 10 проверок OK, код
  завершения 0, `passed: true`.

Границы периодов (блок `split` отчёта, правило 60/20/20 по времени):

| Часть | Строк | Даты | Доля `ArrDelay >= 15` |
|---|---|---|---|
| train | 14 | 2026-01-05 … 2026-01-18 | 0.571 |
| validation | 5 | 2026-01-19 … 2026-01-23 | 0.6 |
| test | 5 | 2026-01-24 … 2026-01-28 | 0.8 |

`time_order_ok: true`.

## 5. Отрицательный сценарий

Нарушение внесено во временную копию, эталонный файл не менялся:

```powershell
Copy-Item data\flights_sample.csv $env:TEMP\bad.csv
(Get-Content $env:TEMP\bad.csv) -replace '^2026-01-05,5,','2026-01-05,25,' | Set-Content $env:TEMP\bad.csv
python -m mlops_team1.validate_data --data $env:TEMP\bad.csv --contract data/contract.json --report $env:TEMP\bad.json
```

Вывод валидатора:

```text
OK   required_columns: ok
OK   extra_columns: ok
OK   minimum_rows: rows=24, minimum=20
OK   row_length: ok
OK   no_missing_values: ok
OK   types: ok
FAIL ranges: 1 violation(s): DepHour line 2: 25 not in [0, 23]
OK   allowed_values: ok
OK   duplicates: ok
OK   sorted: ok
```

Код завершения (`$LASTEXITCODE`): `1`. Нарушена только проверка `ranges`: час вылета 25
выходит за диапазон 0–23, остальные девять проверок прошли. В отчёте
`passed: false`, блок `split` равен `null`, потому что разбиение считается только для
данных, прошедших контракт.

## 6. Обоснование

- **Правило контракта 1.** `DepHour` в диапазоне 0–23: час суток не бывает
  больше 23. Диапазон взят из смысла поля, а не из значений образца.
- **Правило контракта 2.** `ArrDelay` в диапазоне от −180 до 1440 минут и с ролью
  `target_source`: это источник целевой переменной (`ArrDelay >= 15`), а не
  признак. Лишние столбцы запрещены (`allow_extra_columns: false`), поэтому
  `ArrDelay` явно включён в контракт.
- **Риск утечки.** Момент прогноза: за 60 минут до планового вылета. В этот момент
  `ArrDelay` ещё неизвестен, поэтому его нельзя подавать модели как признак.
  Случайное перемешивание строк смешало бы будущее и прошлое, поэтому разбиение
  идёт строго по времени, а отчёт проверяет `max(train) < min(validation)`.
- **Ограничения набора.** Образец состоит из 24 строк и не представителен для
  реальных рейсов. Валидатор принимает `+5` и `1_0` как целые, а неизвестные
  ключи контракта игнорирует молча. Происхождение файла и его владелец не
  установлены (см. `docs/data-card.md`). Набор, вероятно, учебный
  (синтетический): в нём ровно по одной строке на каждую дату подряд с 5 по
  28 января. Это вывод по структуре данных, документального подтверждения нет.

## 7. Использование ИИ

Claude помогал составить структуру контракта и раздела README, найти проблемы
в PR #25 и подготовить текст этой карточки. Запуски (приёмка в чистом клоне,
нарушение во временной копии) выполнены автором лично, текст проверен автором.
