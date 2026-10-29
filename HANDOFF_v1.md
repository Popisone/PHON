# HANDOFF v1 — PHON (Phononic Orchestration Notation)

**Дата:** 2026-10-29  
**Версия:** 0.1.0  
**Статус:** START  
**Лиценз:** CC BY-SA 4.0 (спецификация) / Apache 2.0 (код)

---

## СЕКЦИЯ 0 — ПРАВИЛА И УРОЦИ

Всички правила от `AI_PLAYBOOK.md` v1.0 са в сила.

**Специфични за PHON:**
- **Урок 1:** PHON е декларативен език. Не очаквай последователно изпълнение.
- **Урок 2:** Фазата е първокласна стойност (0 и pi са различни логически състояния).
- **Урок 3:** Компилаторът проверява физическа съвместимост, не само синтаксис.

---

## СЕКЦИЯ 1 — АРХИТЕКТУРА

Три нива: **Medium** (среда) -> **Components** (блокове) -> **Flow** (поток).

### Компоненти на проекта:
| Компонент | Файл | Статус |
| :--- | :--- | :--- |
| Спецификация | `SPECIFICATION.md` | ✅ v0.1 |
| Лексер | `src/phon/lexer.py` | ⏳ TODO |
| Парсер | `src/phon/parser.py` | ⏳ TODO |
| AST | `src/phon/ast_nodes.py` | ⏳ TODO |
| Семантика | `src/phon/semantic.py` | ⏳ TODO |
| Тестове | `tests/test_lexer.py`, `test_parser.py` | ⏳ TODO |
| Примери | `examples/*.phon` | 🟡 and_gate.phon |

### Стек:
- Python 3.10+, `lark`, `pytest`
- Windows 10/11, PowerShell 5.1

---

## СЕКЦИЯ 2 — ТЕКУЩА ЗАДАЧА

**Задача #1: Лексер на PHON**

Definition of Done:
- [ ] `lexer.py` токенизира всички лексеми от EBNF (Раздел 4 от SPECIFICATION.md)
- [ ] `tests/test_lexer.py` съдържа поне 8 теста
- [ ] `pytest tests/test_lexer.py -v` минава без грешки
- [ ] Git commit след успешен тест

**Какво НЕ правим сега:**
- ❌ Парсер (следваща задача)
- ❌ Семантичен анализ
- ❌ Симулация

---

## СЕКЦИЯ 3 — BACKLOG

| # | Задача | Приоритет | Зависи от |
| :--- | :--- | :--- | :--- |
| 1 | Лексер | 🔴 Висока | — |
| 2 | Парсер с lark | 🔴 Висока | #1 |
| 3 | AST класове | 🔴 Висока | #2 |
| 4 | Семантичен анализ | 🟡 Средна | #3 |
| 5 | Генератор JSON конфигурация | 🟡 Средна | #4 |
| 6 | Интеграция phonomena симулатор | 🟡 Средна | #5 |
| 7 | CI/CD (GitHub Actions) | 🟢 Ниска | #1 |
| 8 | Публикуване в Zenodo | 🟡 Средна | SPECIFICATION.md |

---

## СЕКЦИЯ 4 — СРЕДА

- **ОС:** Windows 10/11
- **Python:** 3.10+ (`python --version`)
- **Git:** инсталиран
- **venv:** `C:\Projects\PHON\.venv`

---

## СЕКЦИЯ 5 — КОМАНДИ ЗА СТАРТИРАНЕ

Активиране на venv:
```powershell
cd C:\Projects\PHON
.\.venv\Scripts\Activate.ps1
```

Пускане на тестове:
```powershell
pytest tests/ -v
```

---

## СЕКЦИЯ 6 — GIT

Първи commit:
```powershell
git init
git add .
git commit -m "Initial: PHON project skeleton"
```

**Последни промени:** (няма още)

---

## СЕКЦИЯ 7 — ХРОНОЛОГИЯ НА СЕСИИТЕ

### 2026-10-29 — Сесия 1 (старт)
- Проект стартиран
- Създаден HANDOFF_v1.md
- Следва: лексер
