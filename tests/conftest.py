"""test fixtures and common code"""
import os
import pytest


@pytest.fixture
def connect_params():
    return dict(
        host=os.getenv("MYSQL_HOST", "mysql"),
        user="test",
        password=os.getenv("MYSQL_PASSWORD", ""),
        database="test_mysql",
    )
