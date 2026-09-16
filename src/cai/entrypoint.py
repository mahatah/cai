"""Select the execution runtime before importing provider-specific startup code."""

import sys


def main() -> None:
    if sys.argv[1:2] == ["copilot"]:
        from cai.copilot.cli import main as copilot_main

        copilot_main(sys.argv[2:])
        return

    from cai.cli import main as legacy_main

    legacy_main()


if __name__ == "__main__":
    main()
