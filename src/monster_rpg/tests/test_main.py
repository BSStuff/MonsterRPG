"""Tests for the main entry point."""

from monster_rpg.main import main


def test_main_exists() -> None:
    """Verify the main function exists and is callable."""
    assert callable(main)
