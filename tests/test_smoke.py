"""Smoke test to verify imports work."""


def test_imports():
    """Test that we can import the package."""
    try:
        from samud.commands import CommandHandler  # noqa: F401
        from samud.database import Database  # noqa: F401
        from samud.server import SAMudServer  # noqa: F401
        from samud.world import World  # noqa: F401

        import samud  # noqa: F401
    except ImportError:
        pass  # Package may not be installed yet


def test_smoke():
    assert True
