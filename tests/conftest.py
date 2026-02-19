"""
Pytest configuration and shared fixtures
"""
import pytest
import os
import sys

# Add project root to path for all tests
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from src.core.db_manager import DBManager


@pytest.fixture
def memory_db():
    """Fixture providing an in-memory database for testing"""
    db = DBManager(':memory:')
    yield db
    db.close()


@pytest.fixture
def sample_module(memory_db):
    """Fixture providing a database with a sample knowledge module"""
    module_id = memory_db.insert_knowledge_module("Test Module")
    return memory_db, module_id


@pytest.fixture
def sample_question_data():
    """Fixture providing sample question data"""
    return {
        'question_text': 'What is 2 + 2?',
        'question_type': 'single',
        'difficulty': 'easy',
        'answers': [
            {'text': '3', 'is_correct': False},
            {'text': '4', 'is_correct': True},
            {'text': '5', 'is_correct': False}
        ]
    }
