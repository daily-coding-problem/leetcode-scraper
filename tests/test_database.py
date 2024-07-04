import pytest
from unittest.mock import patch, MagicMock

from leetcode.problem import Problem
from leetcode.study_plan import StudyPlan
from database.database import Database


class TestDatabase:
    @pytest.fixture
    def db(self):
        connection = MagicMock()
        cursor = MagicMock()
        return Database(connection=connection, cursor=cursor)

    def test_insert_problem(self, db):
        problem = Problem(
            id=1,
            title="Two Sum",
            content="Given an array of integers...",
            difficulty="Easy",
            topics=["Array", "Hash Table"],
            companies=["Amazon", "Google"],
            hints=["Try using a hash map"],
        )

        with patch(
            "database.database.execute_insert", return_value=1
        ) as mock_execute_insert:
            problem_id = db.insert_problem(problem)
            assert problem_id == 1
            mock_execute_insert.assert_called_once()

    def test_insert_study_plan(self, db):
        study_plan = StudyPlan(
            slug="leetcode-75",
            name="LeetCode 75",
            description="A study plan to master the most important 75 LeetCode problems.",
            number_of_problems=0,
            number_of_categories=0,
        )

        with patch(
            "database.database.execute_insert", return_value=1
        ) as mock_execute_insert:
            study_plan_id = db.insert_study_plan(study_plan)
            assert study_plan_id == 1
            mock_execute_insert.assert_called_once()

    def test_insert_study_plan_problem(self, db):
        with patch(
            "database.database.execute_query", return_value=True
        ) as mock_execute_query:
            result = db.insert_study_plan_problem(1, 1, "Array and Hash Table")
            assert result is True
            mock_execute_query.assert_called_once()
