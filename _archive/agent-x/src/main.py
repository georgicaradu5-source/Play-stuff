from __future__ import annotations

import argparse
import os
import sys
from typing import Optional

# Allow running as a script by adding src to sys.path
sys.path.insert(0, os.path.dirname(__file__))

from learn import settle, settle_all
from scheduler import load_config, run_once
from util import setup_logger
from x_api import XApi, NullXApi


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Autonomous X Agent (Python/Tweepy)")
    p.add_argument("--config", default=os.path.join(os.path.dirname(__file__), "config.example.yaml"))
    p.add_argument("--mode", choices=["post", "interact", "both"], default="both")
    p.add_argument("--dry-run", choices=["true", "false"], default="true")
    p.add_argument("--settle", help="Settle metrics for a specific post id")
    p.add_argument("--arm", help="Arm to attribute when settling a single post")
    p.add_argument("--settle-all", action="store_true", help="Settle metrics for all posts")
    p.add_argument("--loop", choices=["true", "false"], default="false", help="Run on a schedule loop")
    p.add_argument("--safety", choices=["print-limits", "print-budget"], help="Show last-seen rate limits or monthly budget")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    logger = setup_logger()
    cfg = load_config(args.config)
    dry_run = args.dry_run.lower() == "true"
    xapi = NullXApi() if dry_run else XApi.from_env()

    if args.safety == "print-limits":
        try:
            from rate_limit import get_limits  # type: ignore
            for row in get_limits():
                print(row)
        except Exception as e:
            print("No rate-limit info yet:", e)
        return
    if args.safety == "print-budget":
        try:
            import budget  # type: ignore
            caps = cfg.get("tiers", {}).get(cfg.get("plan", "free"), {}).get("monthly_caps", {})
            budget.configure_caps(caps.get("posts_create"), caps.get("posts_read"))
            create_count, read_count = budget.monthly_counts()
            print({"create_used": create_count, "read_used": read_count, "caps": caps})
        except Exception as e:
            print("Budget not initialized:", e)
        return
    if args.settle and args.arm:
        settle(xapi, args.settle, args.arm)
        logger.info("Settled post %s under arm %s", args.settle, args.arm)
        return
    elif args.settle_all:
        n = settle_all(xapi)
        logger.info("Settled %d posts", n)
        return

    if args.loop.lower() == "true":
        from .scheduler import run_loop

        run_loop(xapi=xapi, cfg=cfg, mode=args.mode, dry_run=dry_run)
    else:
        run_once(xapi=xapi, cfg=cfg, mode=args.mode, dry_run=dry_run)


if __name__ == "__main__":
    main()
