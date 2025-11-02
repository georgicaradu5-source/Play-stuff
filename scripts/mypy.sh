#!/usr/bin/env bash
set -euo pipefail

# Runs mypy against src for parity with CI
mypy src
