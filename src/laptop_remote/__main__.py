"""Allow running the app with ``python -m laptop_remote``."""

import sys

from .cli import main

if __name__ == "__main__":
    raise SystemExit(main())
