from __future__ import annotations

import sys

from app.web_launcher import run_web_app


def main() -> int:
    if "--kivy" in sys.argv:
        from app.gui import NashTrackApp

        NashTrackApp().run()
        return 0

    return run_web_app(
        open_window="--no-open" not in sys.argv,
        wait="--no-wait" not in sys.argv,
    )


if __name__ == "__main__":
    raise SystemExit(main())
