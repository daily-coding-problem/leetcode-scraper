import pytest
from unittest.mock import patch, MagicMock

from database.database import Database
from leetcode.api.configuration import Configuration
from leetcode.leetcode import LeetCode
from leetcode.api.client import Client


class TestLeetCode:
    @pytest.fixture
    def db(self):
        connection = MagicMock()
        cursor = MagicMock()
        return Database(connection=connection, cursor=cursor)

    @pytest.fixture
    def client(self):
        # Use LeetCode Non-Premium account by not providing any credentials
        configuration = Configuration()
        return Client(configuration)

    @pytest.fixture
    def leetcode(self, client, db):
        return LeetCode(client, db)

    def test_fetch_and_store_study_plan(self, leetcode):
        study_plan_slug = "leetcode-75"
        mock_study_plan_details = {
            "name": "LeetCode 75",
            "slug": "leetcode-75",
            "description": "A study plan to master the most important 75 LeetCode problems.",
            "planSubGroups": [
                {
                    "name": "Array and Hash Table",
                    "questions": [
                        {
                            "titleSlug": "two-sum",
                            "title": "Two Sum",
                            "difficulty": "Easy",
                        }
                    ],
                }
            ],
        }

        with patch.object(
            leetcode.client,
            "get_study_plan_details",
            return_value=mock_study_plan_details,
        ), patch.object(
            leetcode, "_fetch_and_store_problem", return_value=MagicMock(id=1)
        ), patch.object(
            leetcode.database, "does_study_plan_exist", return_value=False
        ), patch.object(
            leetcode.database, "insert_study_plan", return_value=1
        ), patch.object(
            leetcode.database, "insert_study_plan_problem", return_value=True
        ):
            study_plan = leetcode.fetch_and_store_study_plan(study_plan_slug)

            assert study_plan.name == "LeetCode 75"
            assert len(study_plan.problems) > 0
