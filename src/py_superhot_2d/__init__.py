"""Superhot 2D - Top-down tactical action in Python. Entrypoint."""

import sys


def main() -> None:
    """Entry point for the application."""
    from py_superhot_2d.game import GameEngine

    engine = GameEngine()
    engine.run()


if __name__ == "__main__":
    main()
