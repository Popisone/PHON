# HANDOFF v2 — PHON (Phononic Orchestration Notation)

**Дата:** 2026-10-30
**Версия:** v0.6.0-docs (patent documentation released)
**Тестове:** 129 passed
**Git:** tag `v0.6.0-docs` = commit `b5f6f24` (annotated, push-нат)
**GitHub:** https://github.com/Popisone/PHON
**Zenodo DOI:** 10.5281/zenodo.23770120 (концептуален, за v0.5.0)
**Лиценз:** Apache 2.0 (код) / CC BY-SA 4.0 (спецификация)

---

## 1. КАКВО Е PHON

Отворен стандарт за декларативен DSL за фононни (акустични) изчислителни вериги.
Три нива: **Medium** (среда) -> **Components** (блокове) -> **Flow** (поток).
AND gate = конструктивна интерференция. Памет = резонатор с capture/read.

---

## 2. ТЕКУЩО СЪСТОЯНИЕ

### Ядро (всичко работи)
- **Lexer** -> **Parser** (Lark LALR + lru_cache, ~2.4ms) -> **Semantic** -> **Emitter** (JSON) -> **Simulator** (idealized physics)
- **FDTD** (`src/phon/fdtd.py`) — 1D FDTD за референтни сравнения
- **Performance:** 27,467 sims/sec (CPU), 0.029ms cached, 24,092x над FDTD

### Езикови features (v0.5)
- v0.2: `->`, `..`, `()`, `-`, `==` запазени в JSON
- v0.3: `+`, `*`, `/`, `<`, `>`, `!=`, `<=`, `>=`; `if` statements
- v0.4: `compressor` (ratio), `channel` (bandwidth); `compress(...)`, `transmit(...)`
- v0.5: `for i from X to Y { ... }` (стриктни bounds, unroll в simulator)

### Примери (examples/)
- `and_gate.phon` — 2 резонатора + детектор (threshold 1.5)
- `memory.phon` — резонатор с capture/read
- `register4.phon` — 4-битов регистър
- `register8.phon` — 8-битов регистър (0xB5 write -> read back)
- `counter4.phon` — conditional increment (if + for)

### ML + интеграции (v0.4-v0.5)
- **Surrogate:** Random Forest + PyTorch NN, R^2 = 1.0000
- **Exports:** `phon_model.onnx` (23 KB), `phon_model.h` (48 KB, ~1263 реда C)
- **REST API:** `api_onnx.py` (FastAPI + ONNX Runtime, без sklearn)
- **Client:** `client_onnx.py`
- **GPU (Kaggle Tesla T4):** 398M sims/sec, 53M predictions/sec

### Патентна документация (v0.6.0-docs — ЗАВЪРШЕНА)
`docs/patent/` съдържа:
- `README.md` — индекс + filing препоръки (EPO/USPTO/PCT) + To-do
- `01_TECHNICAL_DESCRIPTION.md` — 182 реда, 7 секции
- `02_CLAIMS_DRAFT.md` — 12 claims (6 independent + 6 dependent) + Notes for Attorney
- `03_ABSTRACT.md` — ~130 думи (USPTO/EPO compliant)
- `04_FIGURES.md` — 8 фигури с описания за илюстратор

**Заглавие на патента:** "Method and System for Phononic Data Compression and Transmission"

---

## 3. КЛЮЧОВИ ФАЙЛОВЕ

Основен пакет (src/phon/):
- `grammar.lark` — v0.5 правила
- `lexer.py`
- `parser.py` — LALR + fallback към Earley + lru_cache
- `ast_nodes.py` — вкл. Compressor, Channel, ForStmt
- `semantic.py` — duplicates, refs, ratio>0, for bounds
- `emitter.py` — JSON serialization
- `simulator.py` — interference, capture/read, compress, transmit, for
- `fdtd.py` — 1D FDTD reference
- `__init__.py`

Root файлове:
- `api_onnx.py` — FastAPI + ONNX Runtime (v0.5)
- `client_onnx.py`
- `phon_model.onnx` — trained NN (23 KB)
- `phon_model.h` — C header за MCU (48 KB)
- `integration_artifacts/build_artifacts.py`
- `docs/patent/` — v0.6 документация (5 файла)
- `examples/` — 5 .phon файла
- `tests/` — 129 теста

---

## 4. УРОЦИ ОТ СЕСИЯТА (2026-10-30)

1. **venv activation е критичен** — Python 3.14 глобален != venv (3.11). Винаги `where.exe python` първо.
2. **Here-string в PowerShell 5.1** — ползвай literal here-string (at-quote), НЕ expandable here-string (at-doublequote). Дълги текстове се чупят при copy-paste.
3. **Verify преди commit** — 7-секционна проверка хваща проблеми рано.
4. **Tag = HEAD след всички fix-ове** — ако commit-неш fix след tag, retag преди push.
5. **git rm --cached -r src/phon.egg-info/** — изважда от tracking, файловете остават локално.
6. **.gitignore whitelist** — удивителна + път работи само в root, не в подпапка.
7. **LF -> CRLF warning** — нормално за Windows, не блокер.

---

## 5. РАБОТЕН СТИЛ (КРИТИЧНО)

- Отговаряй на **български**
- Давай **PowerShell код** за директен paste, с маркери START/END
- **Backup преди всяка промяна** (`Copy-Item file file.bak-YYYYMMDD_HHMMSS`)
- След всяка промяна: `python -m pytest tests\ -q`
- Ако гръмне: покажи **първите 3 реда** от грешката -> fix
- **Commit + retag + push** след успешен тест
- **Един блок = една стъпка**

---

## 6. КАКВО СЛЕДВА (Приоритети)

### Immediate (следваща сесия, ~1 час)
1. `docs/patent/05_PRIOR_ART_SEARCH.md` — prior art search
2. `docs/patent/06_FILING_CHECKLIST.md` — EPO vs USPTO vs PCT
3. README badge `v0.6.0-docs`
4. Нов Zenodo DOI за v0.6.0-docs

### Извън сесията (ръчно)
- Изпрати `01_TECHNICAL_DESCRIPTION.md` + `02_CLAIMS_DRAFT.md` + `03_ABSTRACT.md` на адвокат
- Изчакай feedback преди да пипаш claims

### След feedback (v0.7)
- `while` цикли
- GDS export (PDK)
- Пълен ONNX API benchmark в README
- Phonomena 1D FDTD интеграция

### Backlog
- `break` / `continue`
- 8-bit ALU пример
- CI/CD (GitHub Actions)

---

## 7. КОМАНДИ ЗА СТАРТИРАНЕ

Стартиране:
- `cd C:\Projects\PHON`
- `.\.venv\Scripts\Activate.ps1`
- `python -m pytest tests\ -q`

Очакван резултат: `129 passed in ~0.4s`

---

## 8. GIT СЪСТОЯНИЕ

- `b5f6f24` (HEAD, tag: `v0.6.0-docs`, origin/main) — docs(patent): fix phon_model.h size
- `14dd5a4` — chore(git): .gitignore + untrack egg-info
- `104c164` — docs(patent): add 01_TECHNICAL_DESCRIPTION
- `ae19e50` — docs(patent): claims + abstract + figures
- `e7a958c` (tag: `v0.5.0`) — baseline

**Remote:** `origin/main` = `b5f6f24` (clean)
**Working tree:** clean

---

## 9. ПЪРВО СЪОБЩЕНИЕ В НОВ ЧАТ

> Продължаваме оттук. Прочети HANDOFF_v2.md.
>
> Следващата задача е docs/patent/05_PRIOR_ART_SEARCH.md — prior art search за:
> - Phononic computing reviews 2023-2025
> - US 2020/008976 A1, US 2019/012345 A1
> - Intel / GlobalFoundries / imec патенти
>
> Давай ми стъпките като PowerShell код за директен paste, с backup преди всяка промяна.
> Here-string: literal (at-quote), не expandable.
