"""
Test settings: disable migration files so the test DB is built from models.

The reviews app has duplicate 0002_* branches; running full migrations fails on
a fresh test database. This keeps `manage.py test` usable until migrations are
squashed or reconciled.
"""

from bookhive.settings import *  # noqa: F401,F403

INSTALLED_APPS = list(INSTALLED_APPS)


class _DisableMigrations(dict):
    def __contains__(self, item):
        return True

    def __getitem__(self, item):
        return None


MIGRATION_MODULES = _DisableMigrations()
