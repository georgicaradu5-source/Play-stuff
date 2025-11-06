# v1.1.0 - ASCII Normalization & Windows Compatibility

## HIGHLIGHTS

**Full Windows Terminal Compatibility** - All documentation and console output now renders correctly without Unicode encoding errors on any platform.

## WHAT'S NEW

### Documentation
- **ASCII-only documentation** - All active docs (README, QUICKSTART) use pure ASCII
- **Windows compatibility** - No more UnicodeEncodeError on Windows PowerShell/cmd
- **Cleaned QUICKSTART** - Removed duplicate content, improved structure, added validation checklist
- **Clearer formatting** - Emoji headings -> ASCII text; Unicode symbols -> ASCII equivalents

### Runtime Improvements
- **ASCII console output** - All status messages use ASCII prefixes: [OK], [ERROR], [WAIT], [SEARCH], [AUTH], [METRICS], [WARNING], [INFO]
- **Fixed scheduler.py** - Removed emoji output causing Windows encoding crashes
- **Fixed rate_limiter.py** - ASCII-only status messages
- **Fixed main.py** - ASCII-only auth flow and metrics output

### Repository Organization
- **Archived legacy docs** - Moved planning documents to legacy/planning/
- **Removed empty placeholders** - Cleaned root directory
- **Restored guides** - Complete public-facing documentation

### Configuration
- **Config loading** - YAML configuration loaded via PyYAML with UTF-8 encoding
- **Optional validation** - Code supports Pydantic validation if config_schema.py module is added (currently uses basic YAML loading with backward compatibility)

## CHANGES IN DETAIL

**Replaced throughout:**
- Right arrows ->
- Em-dashes -
- Multiplication x
- Checkmarks [x]
- Box-drawing chars -> ASCII tree (+--, |)
- Ellipsis ...
- All emoji status indicators -> [PREFIX] format

## VALIDATION RESULTS

**Comprehensive testing confirms production readiness:**

```
[x] Lint:    ruff check src/ tests/ - All checks passed!
[x] Tests:   pytest -v - 18 passed, 2 skipped in 2.39s
[x] Dry-run: Windows PowerShell - Completed with "[OK] Scheduler completed"
[x] ASCII:   Zero non-ASCII in active src/ and docs/ (excluding _archive/)
```

**Test coverage:**
- Reliability layer (retries, rate limits, timeouts, idempotency)
- Telemetry integration (spans, log correlation, graceful fallback)
- Client interactions (GET/POST with retries)

## FILES CHANGED

- README.md - ASCII normalization
- docs/guides/QUICKSTART.md - Complete rewrite
- src/scheduler.py - ASCII console output
- src/rate_limiter.py - ASCII console output
- src/main.py - ASCII console output
- Repository structure cleanup

## BREAKING CHANGES

**None** - All changes are cosmetic/formatting only

## INSTALLATION

```bash
git pull origin main
# No migration needed - just pull and you're good!
```

## FIXED ISSUES

- Windows UnicodeEncodeError in console output
- Duplicated content in QUICKSTART guide
- Emoji-dependent documentation failing on legacy terminals

---

**Full Changelog**: https://github.com/georgicaradu5-source/Play-stuff/compare/a7b71fc...3f729f6
