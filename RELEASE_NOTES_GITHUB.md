# v1.1.0 - ASCII Normalization & Windows Compatibility

## 🎯 Highlights

**Full Windows Terminal Compatibility** - All documentation and console output now renders correctly without Unicode encoding errors on any platform.

## ✨ What's New

### Documentation
- 📝 **ASCII-only documentation** - All active docs (README, QUICKSTART) use pure ASCII
- 🪟 **Windows compatibility** - No more `UnicodeEncodeError` on Windows PowerShell/cmd
- 🧹 **Cleaned QUICKSTART** - Removed duplicate content, improved structure, added validation checklist
- 📋 **Clearer formatting** - Emoji headings → ASCII text; Unicode symbols → ASCII equivalents

### Runtime Improvements
- ✅ **ASCII console output** - All status messages use ASCII prefixes: `[OK]`, `[ERROR]`, `[WAIT]`, `[SEARCH]`, `[AUTH]`, `[METRICS]`, `[WARNING]`, `[INFO]`
- 🔧 **Fixed scheduler.py** - Removed emoji output causing Windows encoding crashes
- 🔧 **Fixed rate_limiter.py** - ASCII-only status messages
- 🔧 **Fixed main.py** - ASCII-only auth flow and metrics output

### Repository Organization
- 📁 **Archived legacy docs** - Moved planning documents to `legacy/planning/`
- 🗑️ **Removed empty placeholders** - Cleaned root directory
- 📚 **Restored guides** - Complete public-facing documentation

### Configuration
- ℹ️ **Config validation**: YAML configuration is loaded and validated at runtime using Pydantic models (see `config_schema.py`)
- ℹ️ **Type safety**: All config fields are type-checked on load with clear error messages for invalid values

## 🔍 Changes in Detail

**Replaced throughout:**
- Right arrows `→` → `->` 
- Em-dashes `—` → `-`
- Multiplication `×` → `x`
- Checkmarks `✅` → `[x]`
- Box-drawing chars → ASCII tree (`+--`, `|`)
- Ellipsis `…` → `...`
- All emoji status indicators → `[PREFIX]` format

## ✅ Validation Results

**Comprehensive testing confirms production readiness:**

```
✓ Lint:    ruff check src/ tests/ - All checks passed!
✓ Tests:   pytest -v - 18 passed, 2 skipped in 2.39s
✓ Dry-run: Windows PowerShell - Completed with "[OK] Scheduler completed"
✓ ASCII:   Zero non-ASCII in active src/ and docs/ (excluding _archive/)
```

**Test coverage:**
- Reliability layer (retries, rate limits, timeouts, idempotency)
- Telemetry integration (spans, log correlation, graceful fallback)
- Client interactions (GET/POST with retries)

## 📦 Files Changed

- `README.md` - ASCII normalization
- `docs/guides/QUICKSTART.md` - Complete rewrite  
- `src/scheduler.py` - ASCII console output
- `src/rate_limiter.py` - ASCII console output
- Repository structure cleanup

## 💥 Breaking Changes

**None** - All changes are cosmetic/formatting only

## 📥 Installation

```bash
git pull origin main
# No migration needed - just pull and you're good!
```

## 🐛 Fixed Issues

- Windows `UnicodeEncodeError` in console output
- Duplicated content in QUICKSTART guide  
- Emoji-dependent documentation failing on legacy terminals

---

**Full Changelog**: https://github.com/georgicaradu5-source/Play-stuff/compare/a7b71fc...30cdb81
