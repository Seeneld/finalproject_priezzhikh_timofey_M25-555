#!/usr/bin/env python3
from valutatrade_hub.cli.interface import run_cli
from valutatrade_hub.logging_config import setup_logging
from valutatrade_hub.parser_service.scheduler import RatesScheduler

scheduler = RatesScheduler(interval_seconds=120)

def main() -> None:
    setup_logging()
    scheduler.start()
    run_cli()
    scheduler.stop()

if __name__ == "__main__":
    main()