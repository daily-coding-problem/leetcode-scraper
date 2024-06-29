from collections import defaultdict
from enum import Enum
from typing import List, Dict

from leetcode.problem import Problem


class Difficulty(Enum):
    EASY = 'easy'
    MEDIUM = 'medium'
    HARD = 'hard'


class StudyPlan:
    def __init__(
        self,
        name: str,
        slug: str = '',
        description: str = '',
        number_of_problems: int = 0,
        number_of_categories: int = 0
    ):
        """
        Initialize a StudyPlan with a given name.

        :param name: The name of the study plan.
        """
        self.name = name
        self.slug = slug
        self.description = description
        self.number_of_problems = number_of_problems
        self.number_of_categories = number_of_categories

        self.problems: Dict[int, List[Problem]] = defaultdict(list)
        self.categories: Dict[str, List[Problem]] = defaultdict(list)

    def add_problem(self, category: str, problem: Problem):
        """
        Add a problem to the study plan, organizing by problem ID and topics.

        :param category: The category of the problem.
        :param problem: The Problem object to add.
        """
        self.problems[problem.id].append(problem)
        self.categories[category].append(problem)

    def get_problems_by_id(self, problem_id: int) -> List[Problem]:
        """
        Retrieve all problems with a specific ID.

        :param problem_id: The ID of the problems to retrieve.
        :return: A list of Problem objects with the given ID.
        """
        return self.problems[problem_id]

    def get_problems_by_category(self, category: str) -> List[Problem]:
        """
        Retrieve all problems related to a specific category.

        :param category: The category of the problems to retrieve.
        :return: A list of Problem objects related to the given category.
        """
        return self.categories[category]

    def get_number_of_problems(self) -> int:
        """
        Get the total number of problems in the study plan.

        :return: The total number of problems.
        """
        return sum(len(problems) for problems in self.problems.values())

    def get_number_of_categories(self) -> int:
        """
        Get the total number of categories in the study plan.

        :return: The total number of categories.
        """
        return len(self.categories)

    def get_problems_by_difficulty(self, difficulty: Difficulty) -> List[Problem]:
        """
        Retrieve all problems related to a specific difficulty.

        :param difficulty: The difficulty of the problems to retrieve.
        :return: A list of Problem objects related to the given difficulty.
        """
        return [
            problem
            for problems in self.problems.values()
            for problem in problems
            if problem.difficulty.lower() == difficulty.value.lower()
        ]

    def to_dict(self):
        return {
            'name': self.name,
            'slug': self.slug,
            'description': self.description,
        }

    def __repr__(self):
        return (
            f"StudyPlan(name={self.name}, "
            f"problems={self.number_of_problems}, "
            f"categories={self.number_of_categories})"
        )
