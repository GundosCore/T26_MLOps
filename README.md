# mlops-team1

Учебный проект команды 1 по курсу MLOps. ЛР1: репозиторий и воспроизводимая среда. ЛР2: контракт данных и проверки качества. ЛР3: версионирование данных (DVC).

## Требования

- Git
- Python **3.12** (проверьте: `python --version`)

## Установка

Клонируйте репозиторий и перейдите в его папку, затем создайте окружение.

Windows PowerShell:

```powershell
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

Linux или macOS:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

После активации в начале строки терминала должно быть `(.venv)`.

## Проверки

```bash
python -m ruff check .
python -m pytest -q
```

Ожидаемый результат: `All checks passed!` и строка `passed` без `failed` и `error`.

## Запуск

```bash
python -c "import mlops_team1; print(mlops_team1.ping())"
```

Ожидаемый вывод: `pong`.

## Данные и контракт (ЛР2)

- `data/contract.json` — машинный контракт данных: поля, типы, диапазоны, версия.
- `data/flights_sample.csv` — учебный образец (24 синтетические строки) под управлением DVC: в Git лежит `data/flights_sample.csv.dvc`, сам файл достаётся командой `dvc pull` (см. раздел «Данные и DVC»). Копия версии v1 для тестов и CI: `tests/fixtures/flights_sample_v1.csv`.
- `docs/data-card.md` — карточка набора данных для человека.
- `docs/leakage-and-split.md` — момент прогноза, разбиение и меры против утечки.

### Проверка данных

```bash
python -m mlops_team1.validate_data --data data/flights_sample.csv --contract data/contract.json --report reports/validation/lr2.json
```

Код завершения 0 означает, что данные соответствуют контракту. Любое нарушение даёт ненулевой код.

### Версии контракта

Версия хранится в поле `contract_version` и меняется осознанно:

- patch: исправление описания без изменения проверки;
- minor: совместимое добавление необязательного поля;
- major: удаление или переименование поля, изменение типа или смысла.

Версия 2.0.0: контракт приведён к курсовой версии. Добавлены метаданные description, owner и source; правила команды sorted и rationale сохранены.

### Отчёты

Отчёты в `reports/` создаются командой выше и в Git не хранятся (каталог указан в `.gitignore`). Отчёт воспроизводится одной командой, а в CI сохраняется как артефакт. Отчёты версий данных ЛР3, которые нужны как доказательство, лежат в `docs/reproducibility/validation/`.

## Данные и DVC

Данные не лежат в Git. Git хранит только «квитанцию» `data/flights_sample.csv.dvc` (хэш и размер файла), а сам файл хранится в DVC cache и в remote. По коммиту Git и квитанции DVC можно восстановить ровно ту версию данных, которая была в этом коммите.

### Как получить данные

1. Клонируйте репозиторий и создайте окружение (см. «Установка»).
2. Установите DVC: `python -m pip install "dvc>=3,<4"`.
3. Распакуйте архив `dvc-storage` **рядом** с клоном: папка `dvc-storage` должна лежать на одном уровне с папкой репозитория, не внутри неё.
4. Выполните `dvc pull`. Ожидаемо: `1 file fetched and 1 file added`.
5. Запустите валидатор:
   ```bash
   python -m mlops_team1.validate_data --data data/flights_sample.csv --contract data/contract.json --report reports/validation/restored.json
   ```
   Код завершения 0, все проверки `OK`. Этот отчёт временный и в Git не попадает.
6. Сверьте SHA-256 файла `data/flights_sample.csv`. В `main` лежит версия v2, поэтому ожидается `bf35cf01db04fb31de810dc16009d643e6bf3be22c791faea7c00fdbc25cff08` (780 байт, в `data/flights_sample.csv.dvc` стоит `md5: 12e7b5a02885ff28f6560bd895a1330e`). Как получить версию v1, описано ниже.
   - PowerShell: `Get-FileHash data\flights_sample.csv -Algorithm SHA256`
   - cmd: `certutil -hashfile data\flights_sample.csv SHA256`

Если `dvc-storage` лежит в другом месте, задайте путь локально: `dvc remote modify --local course-local url <путь>`. Это записывается в `.dvc/config.local` и не коммитится.

### Как получить версию v1

Версия v1 лежит в своём Git-коммите. Перед переключением в проекте не должно быть незакоммиченных изменений.

```bash
git switch --detach a27bc82bb036f1cdb42153757e5abc217ecaa94c
dvc pull
```

Ожидаемо: SHA-256 `d2038bfd4ba28a304e1bed26578c9bfcb556942b51694b8342a75f4f2dbf617e`, размер 482 байта, в `.dvc` стоит `md5: b41ffd893842f7038a7004b9eb1e6628`. Чтобы вернуться к актуальной версии: `git switch main`, затем снова `dvc pull`.

Идентификаторы версий (три разных хеша, ни один не заменяет остальные):

| Версия | Git commit | DVC hash (md5) | SHA-256 CSV | Размер |
|---|---|---|---|---|
| v1 | `a27bc82bb036f1cdb42153757e5abc217ecaa94c` | `b41ffd893842f7038a7004b9eb1e6628` | `d2038bfd4ba28a304e1bed26578c9bfcb556942b51694b8342a75f4f2dbf617e` | 482 байта |
| v2 | `c0224cb1b2537c5f1d0f952957adc20ac153acba` | `12e7b5a02885ff28f6560bd895a1330e` | `bf35cf01db04fb31de810dc16009d643e6bf3be22c791faea7c00fdbc25cff08` | 780 байт |

### Что не коммитить

`.venv`, `.env`, секреты и токены, `.dvc/cache`, `.dvc/config.local`, папку `dvc-storage`, CSV вне `tests/fixtures/`, модели.

### Предупреждение про CRLF

У правильной версии v1 размер 482 байта, у v2 780 байт (окончания строк LF). `dvc pull` возвращает файл байт в байт, поэтому CRLF появляется только если файл открыли и пересохранили в редакторе или создали вручную на Windows. Для DVC это другой файл с другими md5 и SHA-256 (у v1 с CRLF было бы 507 байт). Окончания строк копии v1 в `tests/fixtures/` закреплены в `.gitattributes`.

## Отклонения от задания (ЛР3)

Здесь перечислено, чем проект осознанно отличается от текста методички, и почему. Список показан открыто, чтобы читатель не принимал отличия за ошибки.

- **Имя пакета.** `mlops_team1` вместо `mlops_flight_delay`. Осознанное отличие с ЛР2.
- **Контракт 2.0.0.** Курсовой контракт плюс правила команды `sorted` и `rationale`. По указанию преподавателя.
- **Remote.** Локальная папка `dvc-storage` рядом с клоном, передаётся архивом. В общей конфигурации относительный путь `../../dvc-storage` без секретов. Подтверждено преподавателем.
- **Версия v2.** Синтетическое продолжение v1, генерируется скриптом с фиксированным seed. Разрешено преподавателем.
- **`.gitignore`.** Игнорируются `data/*.csv` и `data/*.parquet` вместо `data/*` с исключениями, иначе DVC не видит свой `.dvc`-файл. Решение команды, преподавателю не согласовывалось.
- **Копия v1 в `tests/fixtures/flights_sample_v1.csv`.** Нужна тестам и CI, потому что CI не имеет доступа к локальному remote. Решение команды.
- **Отчёты валидации в `docs/reproducibility/validation/`.** Потому что `.gitignore` игнорирует любую папку `reports/`. Решение команды.
- **Формат веток.** `<тип>/issue-<номер>-<название>` вместо `lab3/dvc-versioning`.
- **Имя отчёта в CI.** Шаг CI пишет отчёт в `reports/validation/lr2.json`, имя сохранено со времён ЛР2.

## Структура

- `src/mlops_team1/` — код проекта
- `tests/` — тесты
- `.github/workflows/ci.yml` — автоматические проверки (CI)
- `data/` — контракт и `.dvc`-метаданные набора; сами CSV в Git не добавляются, их версионирует DVC (см. `.gitignore`)
- `reports/` — отчёты проверок (создаются командой, в Git не хранятся)
- `docs/` — документация, в том числе `docs/reproducibility/` с протоколом и отчётами версий данных
