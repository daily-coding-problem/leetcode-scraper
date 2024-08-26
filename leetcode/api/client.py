from typing import Dict, Any, List

import requests

from leetcode.api.configuration import Configuration
from leetcode.api.auth import get_csrf_cookie


class Client:
    def __init__(self, configuration: Configuration):
        """
        Initialize the Client with the given configuration.

        :param configuration: A configuration object containing LeetCode session and CSRF token.
        """
        self.configuration = configuration
        leetcode_session = configuration.get("leetcode_session")
        csrf_token = configuration.get("csrf_token")

        if leetcode_session and not csrf_token:
            csrf_token = get_csrf_cookie(leetcode_session)
            configuration.set("csrf_token", csrf_token)

        self.leetcode_session = leetcode_session
        self.csrf_token = csrf_token

    def _get_headers(self) -> Dict[str, str]:
        """
        Returns the headers required for making a request to LeetCode's GraphQL API.

        :return: A dictionary containing the headers.
        """
        return {
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0",
            "x-csrftoken": self.csrf_token,
            "Cookie": f"LEETCODE_SESSION={self.leetcode_session}; csrftoken={self.csrf_token}",
        }

    def get_problem_details(self, slug: str) -> Dict[str, Any]:
        """
        Fetch problem details from LeetCode's GraphQL API using the provided slug.

        :param slug: The slug of the problem.
        :return: A dictionary containing the problem details.
        :raises Exception: If the API request fails or the response does not contain expected data.
        """
        api_url = "https://leetcode.com/graphql"
        query = """
        query getQuestionDetail($titleSlug: String!) {
            question(titleSlug: $titleSlug) {
                questionId
                title
                content
                difficulty
                topicTags {
                    name
                }
                companyTags {
                    name
                }
                hints
            }
        }
        """
        variables = {"titleSlug": slug}
        headers = self._get_headers()

        response = requests.post(
            api_url, json={"query": query, "variables": variables}, headers=headers
        )
        response.raise_for_status()  # Raise an exception for HTTP errors

        response_data = response.json()
        if "data" not in response_data or "question" not in response_data["data"]:
            raise Exception("Problem not found or invalid response format")

        # Add the link to the problem details
        response_data["data"]["question"][
            "link"
        ] = f"https://leetcode.com/problems/{slug}/"

        return response_data["data"]["question"]

    def get_study_plan_details(self, plan_slug: str) -> Dict[str, Any]:
        """
        Fetch study plan details from LeetCode's GraphQL API using the provided plan slug.

        :param plan_slug: The slug of the study plan.
        :return: A dictionary containing the study plan details and the total number of problems.
        :raises Exception: If the API request fails or the response does not contain expected data.
        """
        api_url = "https://leetcode.com/graphql"
        query = """
        query studyPlanDetail($slug: String!) {
            studyPlanV2Detail(planSlug: $slug) {
                slug
                name
                highlight
                staticCoverPicture
                colorPalette
                threeDimensionUrl
                description
                premiumOnly
                needShowTags
                awardDescription
                defaultLanguage
                award {
                    name
                    config {
                        icon
                        iconGif
                        iconGifBackground
                    }
                }
                relatedStudyPlans {
                    cover
                    highlight
                    name
                    slug
                    premiumOnly
                }
                planSubGroups {
                    slug
                    name
                    premiumOnly
                    questionNum
                    questions {
                        translatedTitle
                        titleSlug
                        title
                        questionFrontendId
                        paidOnly
                        id
                        difficulty
                        hasOfficialSolution
                        topicTags {
                            slug
                            name
                        }
                        solutionInfo {
                            solutionSlug
                            solutionTopicId
                        }
                    }
                }
            }
        }
        """
        variables = {"slug": plan_slug}
        headers = self._get_headers()

        response = requests.post(
            api_url, json={"query": query, "variables": variables}, headers=headers
        )
        response.raise_for_status()  # Raise an exception for HTTP errors

        response_data = response.json()
        if (
            "data" not in response_data
            or "studyPlanV2Detail" not in response_data["data"]
        ):
            raise Exception("Study plan not found or invalid response format")

        study_plan_details = response_data["data"]["studyPlanV2Detail"]

        # Calculate the total number of problems in the study plan
        total_problems = sum(
            group.get("questionNum", 0) for group in study_plan_details["planSubGroups"]
        )

        # Add the total number of problems to the study plan details
        study_plan_details["totalProblems"] = total_problems

        return study_plan_details

    def get_recent_questions_for_company(
        self,
        company_slug: str,
        timeframe: str = "six-months",
        difficulties=None,
        top_n: int = 50,
    ) -> Dict[str, Any]:
        """
        Fetch the top N most recently asked questions for a specific company within a given timeframe.

        :param company_slug: The slug of the company (e.g., 'microsoft').
        :param timeframe: The timeframe for questions (e.g., 'last-30-days', 'three-months', 'six-months').
        :param difficulties: The list of difficulties to filter the questions (default is ['EASY', 'MEDIUM']).
        :param top_n: The number of top questions to retrieve (default is 50).
        :return: A dictionary containing the list of questions.
        :raises Exception: If the company does not exist, or the API request fails or the response does not contain expected data.

        """
        if difficulties is None:
            difficulties = ["EASY", "MEDIUM"]

        api_url = "https://leetcode.com/graphql"
        favorite_slug = f"{company_slug}-{timeframe}"
        query = """
        query favoriteQuestionListForCompany($favoriteSlug: String!, $filter: FavoriteQuestionFilterInput) {
          favoriteQuestionList(favoriteSlug: $favoriteSlug, filter: $filter) {
            questions {
              difficulty
              id
              paidOnly
              questionFrontendId
              status
              title
              titleSlug
              translatedTitle
              isInMyFavorites
              frequency
              topicTags {
                name
                nameTranslated
                slug
              }
            }
          }
        }
        """
        variables = {
            "favoriteSlug": favorite_slug,
            "filter": {"difficultyList": difficulties, "positionRoleTagSlug": ""},
        }
        headers = self._get_headers()

        response = requests.post(
            api_url, json={"query": query, "variables": variables}, headers=headers
        )
        response.raise_for_status()  # Raise an exception for HTTP errors

        response_data = response.json()

        if (
            "data" not in response_data
            or response_data["data"].get("favoriteQuestionList") is None
        ):
            raise Exception(
                f"No data found for company '{company_slug}' within the timeframe '{timeframe}'. The company might not exist or no questions are available."
            )

        if "questions" not in response_data["data"]["favoriteQuestionList"]:
            raise Exception("Questions not found or invalid response format")

        # Limit to top N questions
        return response_data["data"]["favoriteQuestionList"]["questions"][:top_n]
