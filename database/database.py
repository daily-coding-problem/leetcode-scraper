import os
import psycopg2
from typing import Any, Dict

from leetcode.problem import Problem
from leetcode.study_plan import StudyPlan


def execute_insert(cursor, connection, sql: str, params: Dict[str, Any]) -> Any:
    """
    Execute an insert query and return the ID of the inserted row.
    :param cursor: The cursor to execute the query.
    :param connection: The connection to commit the transaction.
    :param sql: The SQL query to execute.
    :param params: The parameters to pass to the query.
    :return: The ID of the inserted row, or None if the operation failed.
    """
    try:
        cursor.execute(sql, params)
        result = cursor.fetchone()
        if result is not None:
            result_id = result[0]
            connection.commit()
            return result_id
        else:
            connection.commit()
            return None
    except Exception as e:
        connection.rollback()
        print(f"Error executing insert: {e}")
        return None


def execute_query(cursor, connection, sql: str, params: Dict[str, Any]) -> bool:
    """
    Execute a query and commit the transaction.
    :param cursor: The cursor to execute the query.
    :param connection: The connection to commit the transaction.
    :param sql: The SQL query to execute.
    :param params: The parameters to pass to the query.
    :return: True if the operation was successful, False otherwise.
    """
    try:
        cursor.execute(sql, params)
        connection.commit()
        return True
    except Exception as e:
        connection.rollback()
        print(f"Error executing query: {e}")
        return False


class Database:
    def __init__(self, connection=None, cursor=None):
        if connection is None or cursor is None:
            self.connection = psycopg2.connect(
                dbname=os.getenv("POSTGRES_DB"),
                user=os.getenv("POSTGRES_USER"),
                password=os.getenv("POSTGRES_PASSWORD"),
                host=os.getenv("POSTGRES_HOST"),
                port=os.getenv("POSTGRES_PORT"),
            )
            self.cursor = self.connection.cursor()
        else:
            self.connection = connection
            self.cursor = cursor

    def insert_problem(self, problem: Problem) -> Any | None:
        """
        Insert a problem into the database.
        :param problem: The Problem object to insert.
        :return: The ID of the inserted problem.
        """
        sql = """
        INSERT INTO leetcode.problems (question_id, title, slug, content, difficulty, topics, companies, hints, link)
        VALUES (%(id)s, %(title)s, %(slug)s, %(content)s, %(difficulty)s, %(topics)s, %(companies)s, %(hints)s, %(link)s)
        ON CONFLICT (question_id) DO UPDATE
        SET title = EXCLUDED.title,
            slug = EXCLUDED.slug,
            content = EXCLUDED.content,
            difficulty = EXCLUDED.difficulty,
            topics = EXCLUDED.topics,
            companies = EXCLUDED.companies,
            hints = EXCLUDED.hints,
            link = EXCLUDED.link
        RETURNING id;
        """
        return execute_insert(self.cursor, self.connection, sql, problem.to_dict())

    def insert_study_plan(self, study_plan: StudyPlan) -> Any | None:
        sql = """
        INSERT INTO leetcode.study_plans (slug, name, description)
        VALUES (%(slug)s, %(name)s, %(description)s)
        ON CONFLICT (slug) DO UPDATE
        SET name = EXCLUDED.name,
            description = EXCLUDED.description
        RETURNING id;
        """
        return execute_insert(self.cursor, self.connection, sql, study_plan.to_dict())

    def insert_study_plan_problem(
        self, study_plan_id: int, problem_id: int, category_name: str
    ) -> bool:
        """
        Insert a problem into a study plan.
        :param study_plan_id: The ID of the study plan.
        :param problem_id: The ID of the problem.
        :param category_name: The category of the problem.
        :return: True if the operation was successful, False otherwise.
        """
        sql = """
        INSERT INTO leetcode.study_plan_problems (study_plan_id, problem_id, category_name)
        VALUES (%(study_plan_id)s, %(problem_id)s, %(category_name)s)
        ON CONFLICT (study_plan_id, problem_id) DO UPDATE
        SET category_name = EXCLUDED.category_name;
        """
        return execute_query(
            self.cursor,
            self.connection,
            sql,
            {
                "study_plan_id": study_plan_id,
                "problem_id": problem_id,
                "category_name": category_name,
            },
        )

    def get_problem_by_slug(self, slug: str) -> Problem | None:
        """
        Get a problem from the database by its slug.
        :param slug: The slug of the problem.
        :return: The Problem object with the given slug, or None if not found.
        """
        sql = """
        SELECT * FROM leetcode.problems WHERE slug = %(slug)s;
        """
        self.cursor.execute(sql, {"slug": slug})
        result = self.cursor.fetchone()
        if result is None:
            return None
        return Problem(*result)

    def get_study_plan_by_slug(self, slug: str) -> StudyPlan | None:
        """
        Get a study plan from the database by its slug.
        :param slug: The slug of the study plan.
        :return: The StudyPlan object with the given slug, or None if not found.
        """
        sql = """
        SELECT sp.slug, sp.name, sp.description,
               COUNT(DISTINCT spp.problem_id) AS number_of_problems,
               COUNT(DISTINCT spp.category_name) AS number_of_categories
        FROM leetcode.study_plans sp
        LEFT JOIN leetcode.study_plan_problems spp ON sp.id = spp.study_plan_id
        WHERE sp.slug = %(slug)s
        GROUP BY sp.slug, sp.name, sp.description;
        """
        self.cursor.execute(sql, {"slug": slug})
        result = self.cursor.fetchone()
        if result is None:
            return None
        return StudyPlan(
            slug=result[0],
            name=result[1],
            description=result[2],
            number_of_problems=result[3],
            number_of_categories=result[4],
        )

    def does_problem_exist(self, slug: str) -> bool:
        """
        Check if a problem exists in the database by its slug.
        :param slug: The slug of the problem.
        :return: True if the problem exists, False otherwise.
        """
        sql = """
        SELECT EXISTS(SELECT 1 FROM leetcode.problems WHERE slug = %(slug)s);
        """
        self.cursor.execute(sql, {"slug": slug})

        try:
            result = self.cursor.fetchone()
            return result[0]
        except Exception:
            return False

    def does_study_plan_exist(self, slug: str) -> bool:
        """
        Check if a study plan exists in the database by its slug.
        :param slug: The slug of the study plan.
        :return: True if the study plan exists, False otherwise.
        """
        sql = """
        SELECT EXISTS(SELECT 1 FROM leetcode.study_plans WHERE slug = %(slug)s);
        """
        self.cursor.execute(sql, {"slug": slug})

        try:
            result = self.cursor.fetchone()
            return result[0]
        except Exception:
            return False

    def does_company_exist(self, company: str) -> bool:
        """
        Check if a company exists in the database.
        :param company: The name of the company.
        :return: True if the company exists, False otherwise.
        """
        sql = """
        SELECT EXISTS(SELECT 1 FROM leetcode.companies WHERE name = %(company)s);
        """
        self.cursor.execute(sql, {"company": company})

        try:
            result = self.cursor.fetchone()
            return result[0]
        except Exception:
            return False

    def get_problems_by_company(self, company: str) -> list[Problem]:
        """
        Get a list of problems by a specific company.
        :param company: The name of the company.
        :return: A list of Problem objects.
        """
        sql = """
        SELECT p.id, p.question_id, p.title, p.slug, p.content, p.difficulty, p.topics, p.companies, p.hints, p.link
        FROM leetcode.problems p
        WHERE %(company)s = ANY(p.companies);
        """
        self.cursor.execute(sql, {"company": company})
        results = self.cursor.fetchall()
        return [Problem(*result) for result in results]

    def close(self):
        self.cursor.close()
        self.connection.close()
