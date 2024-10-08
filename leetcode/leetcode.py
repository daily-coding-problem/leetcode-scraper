import multiprocessing
import re
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


def convert_time_frame_to_str(timeframe: str, format_type: str = "default") -> str:
    """
    Convert 30d, 3m, 6m to 'last-30-days', 'three-months', 'six-months'

    :param timeframe: The timeframe to convert.
    :param format_type: The format of the timeframe string.
    :return: The formatted timeframe.
    """
    # Mapping of timeframe abbreviations to their respective string representations
    timeframes_pretty = {"30d": "30 days", "3m": "3 months", "6m": "6 months"}

    timeframes_default = {
        "30d": "last-30-days",
        "3m": "three-months",
        "6m": "six-months",
    }

    # Choose the correct mapping based on the format type
    timeframes = timeframes_pretty if format_type == "pretty" else timeframes_default

    # Return the corresponding string or default to "six-months"
    return timeframes.get(timeframe, "six-months")


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

    def fetch_and_store_company_problems(
        self, company: str, timeframe: str
    ) -> List[Problem]:
        """
        Fetch problems from LeetCode by the company tag and store them in the companies' dictionary.

        :param company: The company tag.
        :param timeframe: The timeframe for questions (e.g., '30d', '3m', '6m').
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

        # convert 30d, 3m, 6m to 'last-30-days', 'three-months', 'six-months'
        timeframe = convert_time_frame_to_str(timeframe)

        questions = _fetch_with_retries(
            lambda: self.client.get_recent_questions_for_company(
                company, timeframe=timeframe
            ),
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

    def _fetch_and_store_problems_for_study_plan(
        self, study_plan_data: dict, add_problem_to_study_plan: callable, plan_slug: str
    ) -> None:
        """
        Fetch and store problems for a study plan using multithreading.

        :param study_plan_data: The raw study plan data fetched from LeetCode.
        :param add_problem_to_study_plan: Function to add a fetched problem to the study plan.
        :param plan_slug: The slug of the study plan.
        """
        print(
            "====================================================================================================="
        )
        number_of_available_cores = multiprocessing.cpu_count()
        # number_of_available_cores = 1 # for testing
        print(f"No. of available threads: {number_of_available_cores}")

        max_threads = min(
            number_of_available_cores,
            len(study_plan_data["planSubGroups"][0]["questions"]),
        )
        print(
            f"Using {max_threads} threads to fetch problems for study plan {plan_slug}"
        )
        print(
            "====================================================================================================="
        )

        # Fetch and store problems using multithreading
        with ThreadPoolExecutor(max_workers=max_threads) as executor:
            future_to_slug = {
                executor.submit(
                    self._fetch_and_store_problem, question["titleSlug"]
                ): question["titleSlug"]
                for category in study_plan_data["planSubGroups"]
                for question in category["questions"]
            }

            for future in as_completed(future_to_slug):
                slug = future_to_slug[future]
                try:
                    problem = future.result()
                    print(f"Fetched problem {problem}")
                    add_problem_to_study_plan(slug, problem)
                    print(f"Added problem {slug} to study plan {plan_slug}")
                except Exception as exc:
                    print(f"Error fetching problem {slug}: {exc}")

    def fetch_and_store_study_plan(self, plan_slug: str) -> StudyPlan:
        """
        Fetch a study plan from LeetCode by its slug and store it in the study plan dictionary.

        :param plan_slug: The slug of the study plan.
        :return: The fetched StudyPlan object.
        """
        if plan_slug in self.study_plans:
            study_plan = self.study_plans[plan_slug]
            print(f"Study plan {study_plan.name} already fetched")
            return study_plan

        if self.database.does_study_plan_exist(plan_slug):
            study_plan = self.database.get_study_plan_by_slug(plan_slug)

            if (
                study_plan.number_of_problems is not None
                and study_plan.number_of_problems
                == study_plan.expected_number_of_problems
            ):
                print(f"Study plan {study_plan.name} already fetched")

                with self.study_plans_lock:
                    self.study_plans[plan_slug] = study_plan

                study_plan.number_of_problems = (
                    self.database.get_problem_count_by_study_plan(study_plan.slug)
                )
                study_plan.number_of_categories = (
                    self.database.get_category_count_by_study_plan(study_plan.slug)
                )

                return study_plan

            print(f"Study plan {study_plan.name} has incorrect number of problems")
            print(f"Re-fetching the missing problems for study plan {study_plan.name}")

            # Fetch the problems for this study plan from the database
            problems = self.database.get_problems_by_study_plan_slug(study_plan.slug)

            study_plan_data = self.client.get_study_plan_details(study_plan.slug)

            problems_from_study_plan = [
                question["titleSlug"]
                for category in study_plan_data["planSubGroups"]
                for question in category["questions"]
            ]

            # Extract slugs from the existing problems
            existing_slugs = {problem.slug for problem in problems}

            # Identify missing problems
            missing_problems = [
                slug for slug in problems_from_study_plan if slug not in existing_slugs
            ]

            # Fetch and store missing problems
            if missing_problems:
                print(
                    f"Fetching {len(missing_problems)} missing problems for study plan {study_plan.name}"
                )

                self._fetch_and_store_problems_for_study_plan(
                    study_plan_data={
                        "planSubGroups": [
                            {
                                "questions": [
                                    {"titleSlug": slug} for slug in missing_problems
                                ]
                            }
                        ]
                    },
                    add_problem_to_study_plan=study_plan.add_problem,
                    plan_slug=plan_slug,
                )

                study_plan.number_of_problems = (
                    self.database.get_problem_count_by_study_plan(study_plan.slug)
                )
                study_plan.number_of_categories = (
                    self.database.get_category_count_by_study_plan(study_plan.slug)
                )

                return study_plan

        # Fetch the study plan details
        study_plan_data = self.client.get_study_plan_details(plan_slug)

        if study_plan_data is None or "name" not in study_plan_data:
            raise Exception("Study plan not found")

        study_plan = StudyPlan(
            name=study_plan_data["name"],
            slug=study_plan_data["slug"],
            description=study_plan_data["description"],
            expected_number_of_problems=study_plan_data["totalProblems"],
        )

        with self.database_lock:
            study_plan_id = self.database.insert_study_plan(study_plan)
        if study_plan_id is None:
            raise Exception(
                "Error inserting study plan into the database (Check the logs)"
            )

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

        # Fetch and store all problems for the study plan
        self._fetch_and_store_problems_for_study_plan(
            study_plan_data=study_plan_data,
            add_problem_to_study_plan=add_problem_to_study_plan,
            plan_slug=plan_slug,
        )

        # Store the study plan in the dictionary
        self.study_plans[plan_slug] = study_plan

        study_plan.number_of_problems = self.database.get_problem_count_by_study_plan(
            study_plan.slug
        )
        study_plan.number_of_categories = (
            self.database.get_category_count_by_study_plan(study_plan.slug)
        )

        return study_plan
