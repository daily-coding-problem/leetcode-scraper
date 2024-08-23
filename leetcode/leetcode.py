import multiprocessing
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List

from requests import HTTPError, RequestException

from leetcode.api.client import Client
from leetcode.problem import Problem
from leetcode.study_plan import StudyPlan

from database.database import Database


def _fetch_with_retries(fetch_func, max_retries=5, delay=2, backoff=2):
    """
    Fetch data with retries in case of rate limiting.

    :param fetch_func: The function to fetch data.
    :param max_retries: The maximum number of retries.
    :param delay: The initial delay between retries.
    :param backoff: The backoff multiplier for the delay.
    :return: The fetched data.
    """
    retries = 0
    while retries < max_retries:
        try:
            return fetch_func()
        except HTTPError as e:
            if e.response.status_code == 429:
                time.sleep(delay)
                delay *= backoff
                retries += 1
            else:
                raise
        except RequestException:
            raise
    raise Exception("Max retries exceeded")


class LeetCode:
    def __init__(self, client: Client, database: Database = None):
        self.client = client
        self.database = database

        self.problems: Dict[str, Problem] = {}
        self.study_plans: Dict[str, StudyPlan] = {}
        self.companies: Dict[str, List[Problem]] = {}

        self.problems_lock = threading.Lock()
        self.study_plans_lock = threading.Lock()
        self.companies_lock = threading.Lock()
        self.database_lock = threading.Lock()

    def _fetch_and_store_problem(self, slug: str) -> Problem:
        """
        Fetch a problem from LeetCode by its slug and store it in the problems' dictionary.

        :param slug: The slug of the problem.
        :return: The fetched Problem object.
        """
        print(f"Fetching problem {slug}")

        with self.problems_lock:
            if slug in self.problems:
                problem = self.problems[slug]
                print(f"Problem {problem.slug} already fetched")
                return problem

        with self.database_lock:
            if self.database.does_problem_exist(slug):
                problem = self.database.get_problem_by_slug(slug)
                print(f"Problem {problem.slug} already fetched")
                with self.problems_lock:
                    self.problems[slug] = problem
                return problem

        question = _fetch_with_retries(lambda: self.client.get_problem_details(slug))

        if "questionId" not in question:
            raise Exception("Problem not found")

        problem_data = {
            "id": question["questionId"],
            "title": question["title"],
            "content": question["content"],
            "difficulty": question["difficulty"],
            "topics": (
                [tag["name"] for tag in question["topicTags"]]
                if question["topicTags"]
                else []
            ),
            "companies": (
                [tag["name"] for tag in question["companyTags"]]
                if question["companyTags"]
                else []
            ),
            "hints": question["hints"] if question["hints"] else [],
        }

        problem = Problem(**problem_data)

        try:
            with self.database_lock:
                problem_id = self.database.insert_problem(problem)
        except Exception as e:
            print(f"Error inserting problem into the database: {e}")
            problem_id = None

        if problem_id is None:
            raise Exception(
                "Error inserting problem into the database (Check the logs)"
            )

        problem.id = (
            problem_id  # Set the ID of the problem to the ID returned by the database
        )

        with self.problems_lock:
            self.problems[slug] = problem  # Store the problem in the dictionary (Cache)

        return problem

    def get_problem(self, slug: str) -> Problem:
        """
        Get the problem with the given slug from the stored problems.

        :param slug: The slug of the problem.
        :return: The Problem object with the given slug, or None if not found.
        """
        return self.problems[slug] if slug in self.problems else None

    def fetch_and_store_company_problems(self, company: str) -> List[Problem]:
        """
        Fetch problems from LeetCode by the company tag and store them in the companies' dictionary.

        :param company: The company tag.
        :return: A dictionary of fetched Problem objects with the company tag as the key.
        """
        with self.companies_lock:
            if company in self.companies:
                print(f"Company {company} problems already fetched")
                return self.companies[company]

        with self.database_lock:
            if self.database.does_company_exist(company):
                company_problems = self.database.get_problems_by_company(company)
                print(f"Company {company} problems already fetched")
                with self.companies_lock:
                    self.companies[company] = company_problems
                return company_problems

        company_problems = []

        questions = _fetch_with_retries(
            lambda: self.client.get_recent_questions_for_company(company)
        )

        if not questions:
            raise Exception("No problems found for the company")

        for question in questions:
            slug = question["titleSlug"]
            problem = self.get_problem(slug) or self._fetch_and_store_problem(slug)
            company_problems[slug].append(problem)

        with self.companies_lock:
            self.companies[company] = company_problems

        return company_problems

    def fetch_and_store_study_plan(self, plan_slug: str) -> StudyPlan:
        """
        Fetch a study plan from LeetCode by its slug and store it in the study plan dictionary.

        :param plan_slug: The slug of the study plan.
        :return: The fetched StudyPlan object.
        """
        with self.study_plans_lock:
            if plan_slug in self.study_plans:
                study_plan = self.study_plans[plan_slug]
                print(f"Study plan {study_plan.name} already fetched")
                return study_plan

        with self.database_lock:
            if self.database.does_study_plan_exist(plan_slug):
                study_plan = self.database.get_study_plan_by_slug(plan_slug)
                print(f"Study plan {study_plan.name} already fetched")
                with self.study_plans_lock:
                    self.study_plans[plan_slug] = study_plan
                return study_plan

        # Fetch the study plan details
        study_plan_data = self.client.get_study_plan_details(plan_slug)

        # Check if the study plan is valid
        if study_plan_data is None or "name" not in study_plan_data:
            raise Exception("Study plan not found")

        # Initialize the StudyPlan object
        study_plan = StudyPlan(
            study_plan_data["name"],
            study_plan_data["slug"],
            study_plan_data["description"],
        )

        with self.database_lock:
            study_plan_id = self.database.insert_study_plan(study_plan)
        if study_plan_id is None:
            raise Exception(
                "Error inserting study plan into the database (Check the logs)"
            )

        # Define a helper function to add problems to the study plan
        def add_problem_to_study_plan(slug: str, problem: Problem):
            for category in study_plan_data["planSubGroups"]:
                for question in category["questions"]:
                    if question["titleSlug"] == slug:
                        study_plan.add_problem(category["name"], problem)

                        with self.database_lock:
                            response = self.database.insert_study_plan_problem(
                                study_plan_id, problem.id, category["name"]
                            )
                        if response is None:
                            raise Exception(
                                "Error inserting study plan problem into the database (Check the logs)"
                            )
                        break

        print(
            "====================================================================================================="
        )
        # Maximum number of available CPU cores
        number_of_available_cores = multiprocessing.cpu_count()
        print(f"No. of available threads: {number_of_available_cores}")

        # Get maximum number of threads to use
        max_threads = min(
            number_of_available_cores, len(study_plan_data["planSubGroups"])
        )
        print(
            f"Using {max_threads} threads to fetch problems for study plan {plan_slug}"
        )
        print(
            "====================================================================================================="
        )

        # Fetch and store problems using multithreading
        with ThreadPoolExecutor(max_workers=max_threads) as executor:
            # Create a dictionary to map futures to their respective slugs
            future_to_slug = {
                executor.submit(
                    self._fetch_and_store_problem, question["titleSlug"]
                ): question["titleSlug"]
                for category in study_plan_data["planSubGroups"]
                for question in category["questions"]
            }

            # Process the completed futures
            for future in as_completed(future_to_slug):
                slug = future_to_slug[future]
                try:
                    # Get the result (problem) from the future
                    problem = future.result()
                    print(f"Fetched problem {problem}")
                    # Add the problem to the study plan
                    add_problem_to_study_plan(slug, problem)
                    print(f"Added problem {slug} to study plan {plan_slug}")
                except Exception as exc:
                    print(f"Error fetching problem {slug}: {exc}")

        print(
            f"Fetched {study_plan.get_number_of_problems()} problems for study plan {plan_slug}"
        )

        # Store the study plan in the dictionary
        with self.study_plans_lock:
            self.study_plans[plan_slug] = study_plan

        # Update the number of problems and categories in the study plan
        study_plan.number_of_problems = study_plan.get_number_of_problems()
        study_plan.number_of_categories = study_plan.get_number_of_categories()

        return study_plan
