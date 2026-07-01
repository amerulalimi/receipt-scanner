from app.worker.bootstrap import validate_worker_runtime

validate_worker_runtime()

import asyncio
import logging

from app.services.receipt_worker import run_worker


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    asyncio.run(run_worker())


if __name__ == "__main__":
    main()
