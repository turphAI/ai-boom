"""
Pytest configuration and hooks for Boom-Bust Sentinel tests.
"""
import pytest


def pytest_addoption(parser):
    """Add custom command line options."""
    parser.addoption(
        "--production",
        action="store_true",
        default=False,
        help="Run tests in production environment"
    )
    parser.addoption(
        "--staging",
        action="store_true",
        default=False,
        help="Run tests in staging environment"
    )


def pytest_configure(config):
    """Configure pytest for deployment verification."""
    # Add custom markers
    config.addinivalue_line("markers", "staging: mark test to run only in staging environment")
    config.addinivalue_line("markers", "production: mark test to run only in production environment")


def pytest_collection_modifyitems(config, items):
    """Modify test collection based on environment."""
    if config.getoption("--staging"):
        # Skip production-only tests
        skip_production = pytest.mark.skip(reason="Skipping production test in staging environment")
        for item in items:
            if "production" in item.keywords:
                item.add_marker(skip_production)
    elif config.getoption("--production"):
        # Skip staging-only tests
        skip_staging = pytest.mark.skip(reason="Skipping staging test in production environment")
        for item in items:
            if "staging" in item.keywords:
                item.add_marker(skip_staging)

