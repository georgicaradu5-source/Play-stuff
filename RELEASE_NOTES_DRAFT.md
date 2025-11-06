# Release Notes - Documentation ASCII Normalization# Release Notes - Documentation ASCII Normalization



## Documentation Improvements## Documentation Improvements



### ASCII-Only Documentation (Windows Compatible)### ASCII-Only Documentation (Windows Compatible)

- **Fixed**: All active documentation now renders correctly on Windows terminals without `UnicodeEncodeError`- **Fixed**: All active documentation now renders correctly on Windows terminals without `UnicodeEncodeError`

- **Changed**: Replaced all emoji headings in README.md with clear ASCII text titles- **Changed**: Replaced all emoji headings in README.md with clear ASCII text titles

- **Changed**: Normalized Unicode symbols to ASCII equivalents throughout documentation:- **Changed**: Normalized Unicode symbols to ASCII equivalents throughout documentation:

  - Right arrows -> `->`  - Right arrows (`→`) replaced with `->`

  - Em-dashes -> `-`  - Em-dashes (`—`) replaced with `-`

  - Multiplication signs -> `x`  - Multiplication signs (`×`) replaced with `x`

  - Box-drawing characters -> ASCII tree notation (`+--`, `|`)  - Box-drawing characters replaced with ASCII tree notation (`+--`, `|`)

  - Checkmark emojis -> `[x]` markdown checkboxes  - Checkmark emojis (`✅`) replaced with `[x]` markdown checkboxes

  - Ellipsis -> `...`  - Ellipsis (`…`) replaced with `...`



### Runtime Console Output### Runtime Console Output

- **Fixed**: Removed emojis from `scheduler.py`, `rate_limiter.py`, and `main.py` console output- **Fixed**: Removed emojis from `scheduler.py` and `rate_limiter.py` console output

- **Changed**: Status messages now use ASCII prefixes: `[OK]`, `[WAIT]`, `[WARNING]`, `[ERROR]`, `[SEARCH]`, `[PAUSED]`, `[AUTH]`, `[METRICS]`, `[INFO]`- **Changed**: Status messages now use ASCII prefixes: `[OK]`, `[WAIT]`, `[WARNING]`, `[ERROR]`, `[SEARCH]`, `[PAUSED]`

- **Impact**: Agent can now run in Windows PowerShell/cmd without encoding crashes- **Impact**: Agent can now run in Windows PowerShell/cmd without encoding crashes



### QUICKSTART Guide Cleanup### QUICKSTART Guide Cleanup

- **Fixed**: Removed duplicated/malformed legacy content from bottom of QUICKSTART.md- **Fixed**: Removed duplicated/malformed legacy content from bottom of QUICKSTART.md

- **Improved**: Streamlined guide structure with clear step-by-step flow- **Improved**: Streamlined guide structure with clear step-by-step flow

- **Changed**: All Unicode arrows and em-dashes normalized to ASCII- **Changed**: All Unicode arrows and em-dashes normalized to ASCII



### Repository Organization### Repository Organization

- **Added**: Archived legacy planning documents to `legacy/planning/` directory- **Added**: Archived legacy planning documents to `legacy/planning/` directory

- **Removed**: Empty placeholder documentation files- **Removed**: Empty placeholder documentation files

- **Restored**: Complete public-facing documentation (README, QUICKSTART, guides)- **Restored**: Complete public-facing documentation (README, QUICKSTART, guides)



## Configuration## Validation



### Config Loading BehaviorAll changes validated with comprehensive test suite:

- **Current**: YAML configuration loaded via PyYAML with UTF-8 encoding- ✅ **Lint**: `ruff check` - All checks passed

- **Optional Validation**: Code includes fallback support for Pydantic validation via `config_schema.py` module (not currently included; uses basic YAML loading with backward compatibility)- ✅ **Tests**: `pytest -v` - 18 passed, 2 skipped

- **No Breaking Changes**: All existing config files continue to work as-is- ✅ **Dry-run**: Windows PowerShell - Completed successfully with no encoding errors

- ✅ **ASCII Scan**: Zero non-ASCII characters in active documentation (README.md, docs/guides/QUICKSTART.md)

## Technical Details- ✅ **Fresh Clone**: Tested end-to-end setup flow confirms old version has emoji bug, new version resolves it



### Files Modified## Files Changed

- `README.md` - Complete ASCII normalization

- `docs/guides/QUICKSTART.md` - Removed duplicates, normalized to ASCII### Documentation

- `src/scheduler.py` - ASCII console output- `README.md` - ASCII normalization, improved structure

- `src/rate_limiter.py` - ASCII console output  - `docs/guides/QUICKSTART.md` - Complete rewrite with ASCII-only content

- `src/main.py` - ASCII console output for auth flow and metrics

### Source Code

### Validation Results- `src/scheduler.py` - ASCII console output

- Lint: `ruff check src/ tests/` - All checks passed- `src/rate_limiter.py` - ASCII console output

- Tests: `pytest -v` - 18 passed, 2 skipped in 2.39s

- Dry-run: Windows PowerShell - Completed successfully with ASCII-only output### Repository Structure

- ASCII compliance: Zero non-ASCII characters in active `src/` and `docs/` (excluding archived code in `_archive/`)- Moved legacy planning docs to `legacy/planning/`

- Cleaned root directory of deprecated/empty files

## Testing Notes

## Commits Included

### Coverage Verified

- Reliability layer (retries, rate limits, timeouts, idempotency)1. `35d324d` - chore: archive legacy planning docs and clean root directory

- Telemetry integration (spans, log correlation, graceful fallback)2. `dc1f81f` - docs: restore public-facing documentation and remove empty placeholders

- Client interactions (GET/POST operations with retry logic)3. `30cdb81` - docs: normalize all active documentation to ASCII-only



### Platforms Tested## Impact Summary

- Windows 11 PowerShell 7.x - No encoding errors

- Windows cmd.exe - ASCII output renders correctly**Before**: Documentation and runtime output contained emojis and Unicode symbols causing `UnicodeEncodeError` on Windows terminals

- Git Bash on Windows - Clean ASCII display

**After**: Full ASCII compatibility ensures the agent works reliably across all platforms and terminal environments

## Migration Guide

**Breaking Changes**: None - all changes are cosmetic/formatting only

**No action required** - This release contains only formatting/documentation changes. Simply pull the latest code:

**Migration Required**: None - users simply pull latest changes

```bash
git pull origin main
```

All existing configuration files, authentication tokens, and data continue to work without modification.
