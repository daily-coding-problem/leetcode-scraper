from typing import Dict, Any

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
        :return: A dictionary containing the study plan details.
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

        return response_data["data"]["studyPlanV2Detail"]
