# Протокол воспроизводимости ЛР3

## 1. Окружение

- **ОС:** Linux (WSL)
- **Python:** 3.12.15
- **DVC:** 3.67.1 (установлен через `pip install "dvc>=3,<4"`)

Команды в разделах 3 и 5 даны для PowerShell (Windows); для Bash (Linux, WSL) отличаются только активация окружения (`python3 -m venv .venv`, `source .venv/bin/activate`), вычисление SHA-256 (`sha256sum data/flights_sample.csv`), код возврата (`echo $?`) и временная папка (`/tmp` вместо `$env:TEMP`).

## 2. Таблица версий данных

| Версия | Git commit | DVC hash (md5) | SHA-256 CSV | Период | Строк | Контракт | Результат |
|--------|------------|----------------|-------------|--------|-------|----------|-----------|
| v1 | `a27bc82bb036f1cdb42153757e5abc217ecaa94c` | `b41ffd893842f7038a7004b9eb1e6628` | `d2038bfd4ba28a304e1bed26578c9bfcb556942b51694b8342a75f4f2dbf617e` | 2026-01-05..2026-01-28 | 24 | 2.0.0 | passed |
| v2 | `c0224cb1b2537c5f1d0f952957adc20ac153acba` | `12e7b5a02885ff28f6560bd895a1330e` | `bf35cf01db04fb31de810dc16009d643e6bf3be22c791faea7c00fdbc25cff08` | 2026-01-05..2026-02-13 | 40 | 2.0.0 | passed |

Размер файла: v1 482 байта, v2 780 байт. Разбиение train/validation/test: v1 14/5/5, v2 24/8/8. Отчёты валидации: `docs/reproducibility/validation/lr3-v1.json` и `lr3-v2.json`. Версия v2 создана скриптом `src/mlops_team1/generate_v2.py` (seed 2026, 16 дней), решение описано в `docs/reproducibility/v2-decision.md`.

## 3. Команды восстановления

### 3.1 Подготовка (один раз)

```powershell
# 1. Распаковать архив dvc-storage рядом с клоном: папка dvc-storage на одном уровне с папкой репозитория
#    Пример: C:\Projects\T26_MLOps и C:\Projects\dvc-storage

# 2. Клонировать репозиторий
git clone https://github.com/GundosCore/T26_MLOps.git
cd T26_MLOps

# 3. Создать окружение и установить зависимости
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
python -m pip install "dvc>=3,<4"

# 4. Только если dvc-storage лежит НЕ рядом с клоном (в Git это не коммитится)
# dvc remote modify --local course-local url C:\путь\к\dvc-storage
```

### 3.2 Восстановление v1

```powershell
git switch --detach a27bc82bb036f1cdb42153757e5abc217ecaa94c
git rev-parse HEAD
dvc pull
Get-FileHash data\flights_sample.csv -Algorithm SHA256
python -m mlops_team1.validate_data --data data/flights_sample.csv --contract data/contract.json --report reports/validation/restored-v1.json
$LASTEXITCODE
git switch main
```

Ожидается: `git rev-parse HEAD` печатает `a27bc82bb036f1cdb42153757e5abc217ecaa94c`; `dvc pull` сообщает `1 file fetched and 1 file added`; SHA-256 равен `D2038BFD…F617E` (PowerShell печатает заглавными буквами); валидатор печатает 10 строк `OK`, код возврата 0.

### 3.3 Восстановление v2

```powershell
git switch --detach c0224cb1b2537c5f1d0f952957adc20ac153acba
git rev-parse HEAD
dvc pull
Get-FileHash data\flights_sample.csv -Algorithm SHA256
python -m mlops_team1.validate_data --data data/flights_sample.csv --contract data/contract.json --report reports/validation/restored-v2.json
$LASTEXITCODE
git switch main
```

Ожидается: `git rev-parse HEAD` печатает `c0224cb1b2537c5f1d0f952957adc20ac153acba`; SHA-256 равен `BF35CF01…5CFF08`; код возврата валидатора 0; в отчёте `rows` равно 40.

После каждого `git switch` данные меняются только командой `dvc pull`: Git переключает `.dvc`-файл, а сам CSV Git не трогает. В `main` лежит v2, поэтому после `git switch main` нужно снова выполнить `dvc pull`. Отчёты `restored-v1.json` и `restored-v2.json` лежат в `reports/`, который Git игнорирует, и в коммит не попадают.

## 4. Чем различаются идентификаторы

| Идентификатор | Что идентифицирует | Где взять |
|---|---|---|
| Git commit | состояние всего проекта: код, контракт, `.dvc`-файл | `git rev-parse HEAD` |
| DVC hash (md5) | объект данных в хранилище; по нему DVC находит файл | поле `md5` в `data/flights_sample.csv.dvc` |
| SHA-256 CSV | байты восстановленного файла; сверка после `dvc pull` доказывает, что файл совпал побайтно | `Get-FileHash`; то же значение записано в поле `sha256` отчёта валидации |

Ни один хеш не заменяет остальные. Git commit меняется при любой правке проекта, даже когда данные те же. DVC hash говорит, какой объект искать, но не доказывает, что восстановленный файл не повреждён. SHA-256 вместе с отчётом валидации связывает конкретный файл с проверкой контракта.

**Чем Git отличается от DVC cache и remote.** Git хранит код, контракт и маленькую «квитанцию» `data/flights_sample.csv.dvc` (хеш и размер), но не сами данные. DVC cache (`.dvc/cache`) это локальная копия объектов данных на машине, в Git она не попадает. Remote (`dvc-storage`, имя `course-local`) это общее хранилище: `dvc push` кладёт в него объекты, `dvc pull` берёт их оттуда на другой машине.

## 5. Отказные сценарии

### 5.1 Файл изменён вручную без `dvc add`

```powershell
Add-Content data\flights_sample.csv "2026-02-14,9,0,10"
dvc status
dvc status --quiet
$LASTEXITCODE
```

Ожидается: `dvc status` печатает `changed outs:` и `modified: data\flights_sample.csv`; `dvc status --quiet` ничего не печатает, код возврата 1. Обычный `dvc status` возвращает код 0 даже при изменениях, поэтому в автоматических проверках нужен `--quiet`.

Вернуть файл: удалить его и снова выполнить `dvc pull`.

```powershell
Remove-Item data\flights_sample.csv
dvc pull
dvc status
```

Ожидается: `dvc status` сообщает `Data and pipelines are up to date.`

Автоматическая проверка: `tests/test_dvc_refusal.py` (во временной папке `dvc init --no-scm`, `dvc add`, правка файла, `dvc status --quiet` возвращает 1). В CI DVC не установлен, поэтому там тест пропускается; локально с установленным DVC он проходит.

### 5.2 Версия нарушает контракт или порядок дат

```powershell
Copy-Item tests\fixtures\flights_sample_v1.csv $env:TEMP\broken.csv
# в копии поменять местами 4-ю и 5-ю строки файла (считая заголовок)
python -m mlops_team1.validate_data --data $env:TEMP\broken.csv --contract data/contract.json --report $env:TEMP\broken.json
$LASTEXITCODE
```

Ожидается: все проверки `OK`, кроме `FAIL sorted: 1 violation(s): FlightDate line 5: 2026-01-07 is earlier than 2026-01-08`, код возврата 1. Копия лежит вне репозитория и в Git не попадает.

Автоматическая проверка: `tests/test_data_contract.py::test_violation_is_detected` (набор `BAD_CASES`, в нём в том числе `unsorted_dates`, `dephour_25`, `duplicate_row`). Каждое нарушение даёт ненулевой код возврата валидатора.

### 5.3 Хранилище недоступно (дополнительно)

```powershell
Rename-Item ..\dvc-storage dvc-storage-hidden
Remove-Item -Recurse -Force .dvc\cache
Remove-Item data\flights_sample.csv
dvc pull
Rename-Item ..\dvc-storage-hidden dvc-storage
dvc pull
```

Ожидается: первый `dvc pull` завершается ошибкой `failed to pull data from the cloud` и предупреждением `Missing cache files` с md5 нужного объекта; после возврата папки на место второй `dvc pull` восстанавливает файл.

## 6. Что передавать коллеге для воспроизведения

- **Через Git:** репозиторий (код, `data/contract.json`, `data/flights_sample.csv.dvc`, `.dvc/config` без секретов).
- **Отдельно архивом:** только папка `dvc-storage`. Перед архивированием выполняется `dvc push`. Внутри должны быть объекты обеих версий: `files/md5/b4/1ffd893842f7038a7004b9eb1e6628` (v1) и `files/md5/12/e7b5a02885ff28f6560bd895a1330e` (v2).
- **Не передавать:** `.dvc/cache`, рабочий `data/flights_sample.csv`, `.dvc/config.local`, `.venv`, секреты.
- Получатель распаковывает `dvc-storage` рядом с клоном (на одном уровне с папкой репозитория) и выполняет шаги раздела 3.
