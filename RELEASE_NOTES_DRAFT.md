# Release Notes - Documentation ASCII Normalization

## Documentation Improvements

### ASCII-Only Documentation (Windows Compatible)
- **Fixed**: All active documentation now renders correctly on Windows terminals without `UnicodeEncodeError`
- **Changed**: Replaced all emoji headings in README.md with clear ASCII text titles
- **Changed**: Normalized Unicode symbols to ASCII equivalents throughout documentation:
  - Right arrows (`→`) replaced with `->`
  - Em-dashes (`—`) replaced with `-`
  - Multiplication signs (`×`) replaced with `x`
  - Box-drawing characters replaced with ASCII tree notation (`+--`, `|`)
  - Checkmark emojis (`✅`) replaced with `[x]` markdown checkboxes
  - Ellipsis (`…`) replaced with `...`

### Runtime Console Output
- **Fixed**: Removed emojis from `scheduler.py` and `rate_limiter.py` console output
- **Changed**: Status messages now use ASCII prefixes: `[OK]`, `[WAIT]`, `[WARNING]`, `[ERROR]`, `[SEARCH]`, `[PAUSED]`
- **Impact**: Agent can now run in Windows PowerShell/cmd without encoding crashes

### QUICKSTART Guide Cleanup
- **Fixed**: Removed duplicated/malformed legacy content from bottom of QUICKSTART.md
- **Improved**: Streamlined guide structure with clear step-by-step flow
- **Changed**: All Unicode arrows and em-dashes normalized to ASCII

### Repository Organization
- **Added**: Archived legacy planning documents to `legacy/planning/` directory
- **Removed**: Empty placeholder documentation files
- **Restored**: Complete public-facing documentation (README, QUICKSTART, guides)

## Validation

All changes validated with comprehensive test suite:
- ✅ **Lint**: `ruff check` - All checks passed
- ✅ **Tests**: `pytest -v` - 18 passed, 2 skipped
- ✅ **Dry-run**: Windows PowerShell - Completed successfully with no encoding errors
- ✅ **ASCII Scan**: Zero non-ASCII characters in active documentation (README.md, docs/guides/QUICKSTART.md)
- ✅ **Fresh Clone**: Tested end-to-end setup flow confirms old version has emoji bug, new version resolves it

## Files Changed

### Documentation
- `README.md` - ASCII normalization, improved structure
- `docs/guides/QUICKSTART.md` - Complete rewrite with ASCII-only content

### Source Code
- `src/scheduler.py` - ASCII console output
- `src/rate_limiter.py` - ASCII console output

### Repository Structure
- Moved legacy planning docs to `legacy/planning/`
- Cleaned root directory of deprecated/empty files

## Commits Included

1. `35d324d` - chore: archive legacy planning docs and clean root directory
2. `dc1f81f` - docs: restore public-facing documentation and remove empty placeholders
3. `30cdb81` - docs: normalize all active documentation to ASCII-only

## Impact Summary

**Before**: Documentation and runtime output contained emojis and Unicode symbols causing `UnicodeEncodeError` on Windows terminals

**After**: Full ASCII compatibility ensures the agent works reliably across all platforms and terminal environments

**Breaking Changes**: None - all changes are cosmetic/formatting only

**Migration Required**: None - users simply pull latest changes
