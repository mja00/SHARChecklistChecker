"""Allow ``python -m shar_checklist``."""

from .cli import main

if __name__ == "__main__":
    raise SystemExit(main())
