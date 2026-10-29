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
| Лексер | `src/phon/lexer.py` | ✅ v0.1 (13 теста) |
| Парсер | `src/phon/parser.py` | ✅ v0.1 (8 теста) |
| AST | `src/phon/ast_nodes.py` | ✅ v0.1 |
| Семантика | `src/phon/semantic.py` | ✅ v0.1 (10 теста) |
| Тестове | `tests/` | ✅ 85 passed (74 + 11 surrogate/isolation) |
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

### 2026-10-29 - Сесия 2 (лексер)
- ✅ `src/phon/lexer.py` — 150 реда, токенизира всички лексеми
- ✅ `tests/test_lexer.py` — 13 теста, всички PASS
- ✅ `conftest.py` + `src/phon/__init__.py`
- ⏳ Следва: парсер с `lark` (Задача #2)

### 2026-10-29 - Сесия 3 (парсер)
- ✅ `src/phon/grammar.lark` — Lark граматика (EBNF -> Lark)
- ✅ `src/phon/ast_nodes.py` — AST dataclass-ове
- ✅ `src/phon/parser.py` — Lark earley парсер + AST builder
- ✅ `tests/test_parser.py` — 8 теста (общо 21 в проекта)
- ⏳ Следва: семантичен анализ (Задача #3 - правила 5.4)

### 2026-10-29 - Сесия 3 (парсер) - завършена
- ✅ `src/phon/grammar.lark` - Lark граматика с COMPONENT_TYPE/UNIT терминали
- ✅ `src/phon/ast_nodes.py` - AST dataclass-ове
- ✅ `src/phon/parser.py` - Lark earley + _find_program + _flatten_stmt
- ✅ `tests/test_parser.py` - 8 теста (общо 21 в проекта)
- 📚 Урок: Lark изхвърля анонимни string литерали от дървото
  -> дефинирай ги като именувани терминали (COMPONENT_TYPE, UNIT)
- ⏳ Следва: семантичен анализ (правила 5.4)

### 2026-10-29 - Сесия 4 (семантика) - завършена
- ✅ `src/phon/semantic.py` - SemanticAnalyzer с 5 проверки
- ✅ `tests/test_semantic.py` - 10 теста (общо 31 в проекта)
- ✅ Проверки: дубликати, interfere refs, emit refs, band freq, detect w/o detector
- ⏳ Следва: генератор на JSON конфигурация (Задача #4)

### 2026-10-29 - Сесия 4 (семантика) - завършена
- ✅ `src/phon/semantic.py` - SemanticAnalyzer с 5 проверки
- ✅ `tests/test_semantic.py` - 10 теста (общо 31 в проекта)
- ✅ Проверки: дубликати, interfere refs, emit refs, band freq, detect w/o detector
- ⏳ Следва: генератор на JSON конфигурация (Задача #4)

### 2026-10-29 - Сесия 6 (симулатор) - завършена
- ✅ `src/phon/simulator.py` - idealized wave physics (complex interference)
- ✅ `tests/test_simulator.py` - 10 теста (общо 51 в проекта)
- ✅ Editable install - `python -m phon.emitter` работи
- ✅ and_gate.phon: threshold 1.5, amp=2.0, AND логика от физика
- 📚 Урок: here-string `n (LF) vs файлове `r`n (CRLF) -> .Contains() не работи
  -> ползвай regex с (?s) или [regex]::Escape.
- ✅ v0.2 FIXED (2026-10-29): `_serialize` запазва ->, .., (), -, ==
  чрез именувани терминали ARROW, RANGE, LPAREN, RPAREN, MINUS, EQ.
  в `path`, `band`, `phase_match`. v0.2: именувани терминали ARROW/RANGE/LPAREN.
- ⏳ Следва: Пример 2 - memory.phon (резонатор, capture/read, state)

### 2026-10-29 - Сесия 7a (capture/read на езиково ниво) - завършена
- ✅ `grammar.lark` - нови capture_stmt, read_stmt
- ✅ `ast_nodes.py` - CaptureStmt, ReadStmt
- ✅ `parser.py` - build branches
- ✅ `semantic.py` - проверки: capture.target/read.source са резонатори
- ✅ `emitter.py` - JSON serialization
- ✅ `examples/memory.phon` - първи пример с памет
- ✅ `tests/test_memory.py` - 8 теста (общо 59)
- ⏳ Следва: Сесия 7b - симулатор със state (capture/read) + simulation тестове

### 2026-10-29 - Сесия 7b (симулатор със state) - завършена
- ✅ `src/phon/simulator.py` - resonators dict + capture/read handlers
- ✅ `tests/test_memory_sim.py` - 10 теста (общо 69 в проекта)
- ✅ `memory.phon` end-to-end: write -> capture -> read -> detect = 1
- ✅ `read` прави snapshot, не препратка (2 независими read-а работят)
- ✅ Два резонатора пазят независими стойности (m1: 5GHz/0, m2: 7GHz/1)
- ⏳ Следва: по-сложен пример (напр. 4-битов брояч) или v0.2 grammar fix

### 2026-10-29 - Сесия 8 (v0.2 grammar fix) - завършена
- ✅ `grammar.lark` - ARROW, RANGE, LPAREN, RPAREN, MINUS, EQ терминали
- ✅ `parser.py` - `_serialize_list` с tight rules + `_semantic_children`
- ✅ `_serialize_func_call` - drop parens за simulator compatibility
- ✅ `tests/test_v02_operators.py` - 5 теста (общо 74)
- 📚 Урок: Lark изхвърля анонимни string литерали; именувани терминали
  се запазват. `_semantic_children` изолира IDENT/expr от пунктуация.
- ⚠️ v0.3 TODO: +, *, /, <, >, !=, <=, >= все още се губят (не се ползват).
- ⏳ Следва: 4-битов брояч ИЛИ phonomena интеграция ИЛИ publish v0.2

### 2026-10-29 - Сесия 9 (surrogate pipeline) - завършена
- ✅ `scripts/generate_phon_dataset.py` - 256 / 1024 samples за < 1s
- ✅ `scripts/train_surrogate.py` - single DecisionTree + analytic fallback
- ✅ `scripts/train_surrogate_v2.py` - 4 модела + feature engineering
- ✅ `scripts/test_local_llm.py` - probe за ollama / nobodywho
- ✅ `tests/test_surrogate_pipeline.py` - 11 теста (общо 85)
- 📊 РЕЗУЛТАТИ (1024 samples):
    - DecisionTree(raw phases):  94.63%
    - DecisionTree(+cos(delta)): 100.00%
    - RandomForest(+cos):        100.00%
    - Analytic rule (physics):   100.00%
- 📚 УРОК: physics-informed feature engineering (cos of phase delta)
  превръща 94.6% -> 100%. Data-driven ML се мъчи с кръгова граница.
- 📚 УРОК: state isolation е коректна. Всеки Simulator е независим.
  cfg НЕ се мутира. Deterministic при повторение.
- 📚 УРОК: 256 samples са insufficient за DecisionTree; 1024 вече помагат,
  но физичната характеристика е истинският ключ.
- ⏳ Следва: (a) 4-битов брояч (композиция), (b) phonomena 1D FDTD,
  (c) publish v0.2, (d) интеграция с локален LLM (нужен Ollama)