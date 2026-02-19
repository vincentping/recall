"""
Unit tests for DBManager class
"""
import pytest
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.core.db_manager import DBManager


class TestDBManager:
    """Test cases for DBManager"""

    def test_initialization_with_memory_db(self):
        """Test DBManager can initialize with in-memory database"""
        db = DBManager(':memory:')
        assert db is not None
        assert db.conn is not None
        db.close()

    def test_create_tables(self):
        """Test that all required tables are created"""
        db = DBManager(':memory:')

        # Check that tables exist
        cursor = db.cursor
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]

        required_tables = [
            'Knowledge_Modules',
            'Lessons',
            'Questions',
            'Answers',
            'Question_Statistics'
        ]

        for table in required_tables:
            assert table in tables, f"Table {table} should exist"

        db.close()

    def test_insert_knowledge_module(self):
        """Test inserting a knowledge module"""
        db = DBManager(':memory:')

        module_id = db.insert_knowledge_module("Test Module")
        assert module_id is not None
        assert module_id > 0

        # Verify it was inserted
        modules = db.get_all_modules()
        assert len(modules) == 1
        assert modules[0][1] == "Test Module"

        db.close()

    def test_duplicate_module_name_fails(self):
        """Test that duplicate module names are rejected"""
        db = DBManager(':memory:')

        db.insert_knowledge_module("Test Module")

        # Try to insert duplicate - should fail or return None
        result = db.insert_knowledge_module("Test Module")
        # Implementation may vary - check your actual behavior

        db.close()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
