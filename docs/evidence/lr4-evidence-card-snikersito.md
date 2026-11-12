# Evidence card ЛР4: трекинг экспериментов в MLflow

## 1. Идентификация

- ФИО: Скворцов Никита
- Группа: Т.МО41
- Команда: 1
- GitHub: `snikersito`
- Роль: Quality and documentation reviewer (загрузка модели из run, тесты, соглашение об MLflow, ревью)
- Контрольная точка: коммит `main` [`742332b`](https://github.com/GundosCore/T26_MLOps/commit/742332b) (все работы ЛР4 слиты)

## 2. Собственный вклад

PR: [#57](https://github.com/GundosCore/T26_MLOps/pull/57) (ветка `chore/issue-50-model-io-docs` → `skvortsov`), затем [#60](https://github.com/GundosCore/T26_MLOps/pull/60) (`skvortsov` → `main`). Связанная задача: #50. Зелёный CI: [run 42511568201](https://github.com/snikersito/T26_MLOps/actions/runs/42511568201).

1. **Загрузка модели и предсказание** `src/mlops_team1/model_io.py` (новый файл), коммит [`7ba6174`](https://github.com/GundosCore/T26_MLOps/commit/7ba6174):
   - `load_bundle` (строки 27–35) читает `model.joblib` и проверяет, что в нём есть все 7 обязательных ключей (`REQUIRED_KEYS`, строки 16–24);
   - `predict_proba_row` (строки 38–45) проверяет входные значения (`DepHour` от 0 до 23, `IsWeekend` равен 0 или 1) и возвращает вероятность опоздания;
   - `download_model` (строки 48–64) скачивает `model/model.joblib` из артефактов run по `--run-id`;
   - `main` (строки 77–92) возвращает код 0 и печатает `bundle_version` и `probability`, а при ошибке выдаёт код 2 и строку `ERROR: …`.
2. **Тесты** `tests/test_model_io.py`, коммит [`e2ccb73`](https://github.com/GundosCore/T26_MLOps/commit/e2ccb73), 7 тестов:
   - все ключи на месте (строка 19);
   - нет ключа `model` → `ValueError` (строка 25);
   - вероятность в диапазоне 0..1 (строка 34);
   - неверные `dep_hour`/`is_weekend` → `ValueError` (строки 40–41);
   - CLI возвращает 0 (строка 48);
   - нет файла → код 2 (строка 57).
3. **Соглашение об экспериментах** `docs/experiments/mlflow-conventions.md` (новый файл), коммит [`795e209`](https://github.com/GundosCore/T26_MLOps/commit/795e209):
   - имена experiment и run (строки 5–9);
   - 8 тегов с источником каждого (10–24);
   - параметры, метрики, inputs, артефакты (25–33);
   - запуск сервера и обучения (34–52);
   - загрузка модели (53–63);
   - что не коммитить (64–67);
   - почему test закрыт (68–).
4. **README**, тот же коммит: разделы «Эксперименты (ЛР4)» (строка 141) и «Отклонения от задания (ЛР4)» (строка 151), остальные разделы не тронуты.

## 3. Проверка коллег

- **PR [#51](https://github.com/GundosCore/T26_MLOps/pull/51), Станислав, обучение с MLflow.** Нашёл утечку: граница разбиения в обучении не сдвигалась до конца дня, поэтому при четырёх рейсах в день один и тот же день попадал и в train, и в validation. Валидатор при этом сдвигал границу, то есть обучение и отчёт валидатора делили данные по-разному. Станислав исправил это в PR [#53](https://github.com/GundosCore/T26_MLOps/pull/53) общей функцией `split_cuts`, я проверил исправление.
- **PR [#61](https://github.com/GundosCore/T26_MLOps/pull/61), сравнение run (работа Владимира).** Сверил файл с версией из прошедшего ревью #58. Проверил арифметику: при precision 1.0 и recall 3/7 F1 = 0.6, а разница ROC AUC 0.571429 → 0.714286 равна одному шагу 1/7 (7 опоздавших и 1 нет в validation). Отметил, что в описании PR не подставлена ссылка на CI.
- **PR [#62](https://github.com/GundosCore/T26_MLOps/pull/62), тесты Екатерины.** Сверил с #59. Проверил, что все сообщения об ошибках, которые ждут тесты, есть в `evaluate.py` и `train.py`. Проверил, что случай `single_class_validation` действительно делает validation одноклассовой. Слил #60, #61 и #62 вместе у себя: конфликтов нет.

## 4. Воспроизведение

```powershell
git fetch upstream
git switch --detach 742332b
python -m pip install -e ".[dev,tracking]"
ruff check .
pytest -q
```

Сквозная проверка (сервер запускается из папки вне репозитория):

```powershell
mlflow server --host 127.0.0.1 --port 5000 --backend-store-uri sqlite:///mlflow.db --default-artifact-root ./mlartifacts
$env:MLFLOW_TRACKING_URI="http://127.0.0.1:5000"
python -m mlops_team1.train_mlflow --data data/flights_sample.csv --contract data/contract.json --experiment mlops-tmo41-team1-flight-delay --max-depth 4
python -m mlops_team1.model_io --run-id <RUN_ID> --dep-hour 10 --is-weekend 0
```

Мой результат (Windows):

- `ruff check .`: All checks passed; `pytest`: 55 passed, 1 skipped (тест DVC пропускается без хранилища) на моей ветке до слияния с работами коллег;
- run появился в эксперименте `mlops-tmo41-team1-flight-delay`, у него 8 тегов, артефакт `model/model.joblib` на месте;
- `model_io --run-id <RUN_ID>` вывел `bundle_version=0.2.0` и `probability=0.7479`, код 0.

## 5. Отрицательный сценарий

Загрузка из несуществующего файла и несуществующего run:

```powershell
python -m mlops_team1.model_io --path nope.joblib
$LASTEXITCODE
python -m mlops_team1.model_io --run-id 00000000000000000000000000000000
$LASTEXITCODE
```

Результат: в обоих случаях код 2 и одна строка `ERROR: …` без трассировки: `ERROR: FileNotFoundError: …` для файла и `ERROR: ValueError: Не удалось скачать модель из run …` для run. Без обёртки в `download_model` (строки 62–63) неизвестный run падал бы с исключением MLflow и трассировкой. Это записано как отклонение в README и в PR #57. Случай с файлом закреплён тестом `test_main_returns_2_for_missing_file`, случай с файлом без ключа `model` закреплён тестом `test_load_bundle_rejects_file_without_model`.

## 6. Обоснование

- **Почему модель грузится из артефакта run, а не из локального файла.** Run хранит модель вместе с параметрами, метриками и тегами (`git.commit`, `data.dvc_hash`, `data.sha256`), поэтому по одному run ID видно, на каком коде и данных она обучена. Локальный файл можно перезаписать незаметно.
- **Зачем проверять ключи и входные значения.** Битый или чужой файл и неверный ввод должны давать понятную ошибку с кодом 2, а не тихий неверный результат.
- **Почему test закрыт.** Конфигурации сравниваются только по validation. Если выбирать по test, он перестаёт быть честной оценкой. В validation v2 всего 8 строк, ROC AUC меняется шагами по 1/7, поэтому выбор предварительный.
- **Альтернатива.** `mlflow.sklearn.log_model` сохранил бы модель в формате MLflow с сигнатурой. В команде модель сохраняется как `joblib`-бандл: в нём, кроме модели, лежат признаки, версия и границы разбиения, поэтому загрузка идёт через `download_artifacts`.

## 7. Использование ИИ

Использовал нейросеть: она подготовила черновики `model_io.py`, тестов, `mlflow-conventions.md`, разделов README, описаний PR, текстов ревью и этой карточки, а также помогла найти утечку в PR #51 и исправить замечание Ruff TRY004. Сам: запускал `ruff`, `pytest`, сервер MLflow, обучение и `model_io` на своём компьютере, делал коммиты и PR. Читал `model_io.py` и могу объяснить, как модель скачивается из run, зачем проверяются ключи и почему ошибка MLflow превращается в код 2.
