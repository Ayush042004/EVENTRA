"""Alembic Migration Verification Tests"""
import os
import tempfile
from pathlib import Path
import pytest
from alembic.config import Config
from alembic import command
from sqlalchemy import create_engine, inspect


def test_alembic_upgrade_downgrade_cycle():
    """Verifies that all Alembic migrations apply and roll back cleanly."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp_db:
        tmp_db_path = tmp_db.name

    try:
        db_url = f"sqlite:///{tmp_db_path}"
        api_dir = Path(__file__).resolve().parents[1]
        alembic_ini_path = api_dir / "alembic.ini"

        alembic_cfg = Config(str(alembic_ini_path))
        alembic_cfg.set_main_option("sqlalchemy.url", db_url)
        alembic_cfg.set_main_option("script_location", str(api_dir / "alembic"))

        # 1. Upgrade to head
        command.upgrade(alembic_cfg, "head")

        engine = create_engine(db_url)
        inspector = inspect(engine)
        tables = set(inspector.get_table_names())

        expected_phase1_tables = {
            "users",
            "events",
            "roles",
            "permissions",
            "role_permissions",
            "event_members",
            "requirements",
            "constraints",
            "objectives",
            "tasks",
            "task_dependencies",
            "resources",
            "budget_items",
            "venues",
            "vendors",
            "vendor_assignments",
            "state_transitions",
        }
        assert expected_phase1_tables.issubset(tables), f"Missing tables: {expected_phase1_tables - tables}"

        # 2. Downgrade Phase 1 migration
        command.downgrade(alembic_cfg, "0001_phase3")
        inspector = inspect(engine)
        tables_after_downgrade = set(inspector.get_table_names())
        assert "users" not in tables_after_downgrade
        assert "tasks" not in tables_after_downgrade
        assert "task_dependencies" not in tables_after_downgrade

        # 3. Upgrade back to head
        command.upgrade(alembic_cfg, "head")
        inspector = inspect(engine)
        tables_reupgraded = set(inspector.get_table_names())
        assert expected_phase1_tables.issubset(tables_reupgraded)
        engine.dispose()

    finally:
        try:
            if 'engine' in locals():
                engine.dispose()
        except Exception:
            pass
        if os.path.exists(tmp_db_path):
            try:
                os.remove(tmp_db_path)
            except Exception:
                pass
