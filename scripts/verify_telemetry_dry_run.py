#!/usr/bin/env python3
"""Verify telemetry output in dry-run mode.

This script runs the X agent in dry-run mode with telemetry enabled
and verifies that OpenTelemetry trace_id and span_id are present in the output.

Usage:
    python scripts/verify_telemetry_dry_run.py

Environment Variables:
    TELEMETRY_ENABLED: Set to 'true' to enable telemetry (default: true)
    OTEL_SERVICE_NAME: Service name for tracing (default: x-agent-dryrun-test)
    X_AUTH_MODE: Auth mode to use (default: tweepy)

Exit Codes:
    0: Success - telemetry traces found
    1: Failure - no traces found or command failed
"""

import os
import re
import subprocess
import sys
from pathlib import Path


def main() -> int:
    """Run dry-run and verify telemetry output."""
    # Set environment for telemetry
    env = os.environ.copy()
    env["TELEMETRY_ENABLED"] = env.get("TELEMETRY_ENABLED", "true")
    env["OTEL_SERVICE_NAME"] = env.get("OTEL_SERVICE_NAME", "x-agent-dryrun-test")
    env["X_AUTH_MODE"] = env.get("X_AUTH_MODE", "tweepy")

    # Ensure we're in the project root
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    os.chdir(project_root)

    print("🔍 Verifying telemetry in dry-run mode...")
    print(f"   TELEMETRY_ENABLED={env['TELEMETRY_ENABLED']}")
    print(f"   OTEL_SERVICE_NAME={env['OTEL_SERVICE_NAME']}")
    print(f"   X_AUTH_MODE={env['X_AUTH_MODE']}")
    print()

    # Run the agent in dry-run mode
    cmd = [
        sys.executable,
        "src/main.py",
        "--dry-run", "true",
        "--mode", "both",
    ]

    print(f"Running: {' '.join(cmd)}")
    print("=" * 60)

    try:
        result = subprocess.run(
            cmd,
            env=env,
            capture_output=True,
            text=True,
            timeout=60,
        )
    except subprocess.TimeoutExpired:
        print("❌ Command timed out after 60 seconds", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"❌ Failed to run command: {e}", file=sys.stderr)
        return 1

    # Combine stdout and stderr for analysis
    output = result.stdout + result.stderr

    print(output)
    print("=" * 60)
    print()

    # Look for telemetry patterns
    trace_id_pattern = re.compile(r'trace_id[=:]?\s*([0-9a-f]{32})', re.IGNORECASE)
    span_id_pattern = re.compile(r'span_id[=:]?\s*([0-9a-f]{16})', re.IGNORECASE)

    trace_ids = trace_id_pattern.findall(output)
    span_ids = span_id_pattern.findall(output)

    # Report findings
    print("📊 Telemetry Verification Results:")
    print(f"   trace_id instances found: {len(trace_ids)}")
    print(f"   span_id instances found: {len(span_ids)}")
    print()

    if trace_ids:
        print(f"✅ Found trace_id(s): {trace_ids[:3]}")  # Show first 3
        if len(trace_ids) > 3:
            print(f"   ... and {len(trace_ids) - 3} more")

    if span_ids:
        print(f"✅ Found span_id(s): {span_ids[:3]}")  # Show first 3
        if len(span_ids) > 3:
            print(f"   ... and {len(span_ids) - 3} more")

    print()

    # Check for W3C TraceContext format in logs
    traceparent_pattern = re.compile(r'traceparent:\s*00-([0-9a-f]{32})-([0-9a-f]{16})-[0-9a-f]{2}')
    traceparents = traceparent_pattern.findall(output)

    if traceparents:
        print(f"✅ Found W3C TraceContext traceparent headers: {len(traceparents)}")
        print()

    # Success criteria: at least one trace_id and one span_id
    if trace_ids and span_ids:
        print("✅ SUCCESS: Telemetry is working correctly in dry-run mode!")
        print(f"   Found {len(trace_ids)} trace IDs and {len(span_ids)} span IDs")
        return 0
    else:
        print("⚠️  WARNING: Telemetry output not found or incomplete", file=sys.stderr)
        print()
        print("This could mean:", file=sys.stderr)
        print("  - Telemetry is disabled (check TELEMETRY_ENABLED env var)", file=sys.stderr)
        print("  - OpenTelemetry packages not installed (pip install -e .[telemetry])", file=sys.stderr)
        print("  - Agent failed before emitting telemetry", file=sys.stderr)
        print()

        if result.returncode != 0:
            print(f"Command exited with code {result.returncode}", file=sys.stderr)

        return 1


if __name__ == "__main__":
    sys.exit(main())
