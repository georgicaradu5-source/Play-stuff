# Release Notes - Documentation ASCII Normalization

## Documentation Improvements

### ASCII-Only Documentation (Windows Compatible)
- **Fixed**: All active documentation now renders correctly on Windows terminals without UnicodeEncodeError
- **Changed**: Replaced all emoji headings in README.md with clear ASCII text titles
- **Changed**: Normalized Unicode symbols to ASCII equivalents throughout documentation

### Runtime Console Output
- **Fixed**: Removed emojis from scheduler.py, rate_limiter.py, and main.py console output
- **Changed**: Status messages now use ASCII prefixes: [OK], [WAIT], [WARNING], [ERROR], [SEARCH], [PAUSED], [AUTH], [METRICS], [INFO]
- **Impact**: Agent can now run in Windows PowerShell/cmd without encoding crashes

### QUICKSTART Guide Cleanup
- **Fixed**: Removed duplicated/malformed legacy content from bottom of QUICKSTART.md
- **Improved**: Streamlined guide structure with clear step-by-step flow
- **Changed**: All Unicode arrows and em-dashes normalized to ASCII

### Repository Organization
- **Added**: Archived legacy planning documents to legacy/planning/ directory
- **Removed**: Empty placeholder documentation files
- **Restored**: Complete public-facing documentation (README, QUICKSTART, guides)

## Configuration

### Config Loading Behavior
- **Current**: YAML configuration loaded via PyYAML with UTF-8 encoding
- **Optional Validation**: Code includes fallback support for Pydantic validation via config_schema.py module (not currently included; uses basic YAML loading with backward compatibility)
- **No Breaking Changes**: All existing config files continue to work as-is

## Technical Details

### Files Modified
- README.md - Complete ASCII normalization
- docs/guides/QUICKSTART.md - Removed duplicates, normalized to ASCII
- src/scheduler.py - ASCII console output
- src/rate_limiter.py - ASCII console output
- src/main.py - ASCII console output for auth flow and metrics

### Validation Results
- Lint: ruff check src/ tests/ - All checks passed
- Tests: pytest -v - 18 passed, 2 skipped in 2.39s
- Dry-run: Windows PowerShell - Completed successfully with ASCII-only output
- ASCII compliance: Zero non-ASCII characters in active src/ and docs/ (excluding archived code in _archive/)

## Testing Notes

### Coverage Verified
- Reliability layer (retries, rate limits, timeouts, idempotency)
- Telemetry integration (spans, log correlation, graceful fallback)
- Client interactions (GET/POST operations with retry logic)

### Platforms Tested
- Windows 11 PowerShell 7.x - No encoding errors
- Windows cmd.exe - ASCII output renders correctly
- Git Bash on Windows - Clean ASCII display

## Migration Guide

**No action required** - This release contains only formatting/documentation changes. Simply pull the latest code:

```bash
git pull origin main
```

All existing configuration files, authentication tokens, and data continue to work without modification.
