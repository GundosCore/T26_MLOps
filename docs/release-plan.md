# План ЛР1: Репозиторий команды и воспроизводимая среда

## Участники и задачи

| Участник | Роль | Issue | PR | Срок | Статус |
|----------|------|-------|-----|------|--------|
| Станислав Соловцов | Repository administrator, Environment engineer | [#1](https://github.com/GundosCore/T26_MLOps/issues/1) | [#2](https://github.com/GundosCore/T26_MLOps/pull/2) | 08.10.2026 | ✅ Готово (merged) |
| Владимир Псюрников | Quality Engineer | [#3](https://github.com/GundosCore/T26_MLOps/issues/3) | [#4](https://github.com/GundosCore/T26_MLOps/pull/4) | 12.10.2026 | Влит в ветку участника, ждёт PR в main |
| Екатерина Головатенко | Release lead | [#5](https://github.com/GundosCore/T26_MLOps/issues/5) | [#6](https://github.com/GundosCore/T26_MLOps/pull/6) | 09.10.2026 | ✅ Готов к мержу |
| Никита Скворцов | Documentation and risk reviewer | [#7](https://github.com/GundosCore/T26_MLOps/issues/7) | [#8](https://github.com/GundosCore/T26_MLOps/pull/8) | 10.10.2026 | ✅ Влит в ветку участника, ждёт PR в main |

## Чек-лист выпуска

- [ ] Все PR участников замержены в `main`
- [ ] CI зелёный для всех PR
- [ ] Все Issues закрыты (через `Closes #...` в PR)
- [ ] Ссылки на PR добавлены в SKIF
- [ ] Создан тег `lr1-v1` на проверенном коммите
- [ ] Evidence cards заполнены всеми участниками

## Риски

1. **Риск:** Кто-то не закроет свой Issue → тег `lr1-v1` не сможет быть поставлен.
   **Решение:** Контролировать связи issue-PR, напоминать участникам.

2. **Риск:** Прямой push в `main` в обход PR.
   **Решение:** Настраиваются тимлидом после слияния PR участников

3. **Риск:** Секреты или `.venv` попадут в Git.
   **Решение:** Проверять diff в каждом PR, `.gitignore` настроен.
