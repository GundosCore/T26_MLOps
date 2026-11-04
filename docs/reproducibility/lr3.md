# Протокол воспроизводимости ЛР3

## 1. Окружение
- **ОС:** Linux (WSL)
- **Python:** 3.12.15
- **DVC:** 3.67.1

## 2. Таблица версий данных

| Версия | Git commit | DVC hash (md5) | SHA-256 CSV | Период | Строк | Контракт | Результат |
|--------|------------|----------------|-------------|--------|-------|----------|-----------|
| v1     | `a27bc82bb036f1cdb42153757e5abc217ecaa94c` | `b41ffd893842f7038a7004b9eb1e6628` | `d2038bfd4ba28a304e1bed26578c9bfcb556942b51694b8342a75f4f2dbf617e` | 2026-01-05..2026-01-28 | 24 | 2.0.0 | passed |
| v2     | `c0224cb1b2537c5f1d0f952957adc20ac153acba` | `12e7b5a02885ff28f6560bd895a1330e` | `bf35cf01db04fb31de810dc16009d643e6bf3be22c791faea7c00fdbc25cff08` | 2026-01-05..2026-02-13 | 40 | 2.0.0 | passed |

## 3. Команды восстановления (Bash)
```bash
git clone https://github.com/GundosCore/T26_MLOps.git
cd T26_MLOps
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -e ".[dev]"
python3 -m pip install "dvc>=3,<4"
git switch --detach c0224cb1b2537c5f1d0f952957adc20ac153acba
dvc pull
sha256sum data/flights_sample.csv
python3 -m mlops_team1.validate_data --data data/flights_sample.csv --contract data/contract.json --report docs/reproducibility/validation/restored-v2.json
git switch main

## 4. Различия идентификаторов

| Идентификатор | Что идентифицирует |
|---------------|-------------------|
| **Git commit** | Состояние всего проекта (код, конфиги, `.dvc` файлы) |
| **DVC hash (md5)** | Объект данных в DVC cache, используется для поиска в remote |
| **SHA-256 файла** | Конкретный CSV файл на диске, гарантирует целостность |

## 5. Отказные сценарии

1. **Изменение CSV без `dvc add`**: `dvc status --quiet` возвращает код `1`, обычный `dvc status` показывает `modified`. Решение: `rm data/flights_sample.csv && dvc pull`.
2. **Нарушение контракта (сортировки)**: Ручная перестановка строк в CSV. Валидатор возвращает код `1` и ошибку `FAIL sorted`.

## 6. Что передавать коллеге

**Нужно передать:** Архив папки `dvc-storage` и Git репозиторий.
**НЕЛЬЗЯ передавать:** Папку `.dvc/cache`, сам файл `data/flights_sample.csv`, файл `.dvc/config.local`, папку `.venv`.