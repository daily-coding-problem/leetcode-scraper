import os
import argparse
from dotenv import load_dotenv

from leetcode.api.client import Client
from leetcode.api.configuration import Configuration
from leetcode.leetcode import LeetCode
from utilities import print_random_banner
from utilities.poetry import get_name, get_description, get_authors, get_version

# Load environment variables
load_dotenv()


def main(csrf_token, leetcode_session, plans):
    if not leetcode_session and not csrf_token:
        print(
            "Using Non-Premium LeetCode account. Some premium only data will not be returned."
        )
        print(
            "====================================================================================================="
        )

    configuration = Configuration()
    configuration.auth["csrf_token"] = csrf_token
    configuration.auth["leetcode_session"] = leetcode_session

    client = Client(configuration)
    leetcode = LeetCode(client)

    for plan in plans:
        print(f"Fetching study plan problems: {plan}")
        try:
            study_plan = leetcode.fetch_and_store_study_plan(plan)
            print(
                "====================================================================================================="
            )
            print(study_plan)
        except Exception as e:
            print(e)


if __name__ == "__main__":
    project_name = get_name().replace("-", " ")
    print_random_banner(project_name)
    print(f"{get_name()} v{get_version()}")
    print(f"{get_description()}")
    print(f"Author(s): {get_authors()}")
    print(
        "====================================================================================================="
    )

    parser = argparse.ArgumentParser(
        description="Fetch and store LeetCode study plan details."
    )
    parser.add_argument(
        "--csrf_token",
        type=str,
        default=os.getenv("CSRF_TOKEN"),
        help="CSRF token for authentication",
    )
    parser.add_argument(
        "--leetcode_session",
        type=str,
        default=os.getenv("LEETCODE_SESSION"),
        help="LeetCode session cookie",
    )
    parser.add_argument(
        "--plans",
        type=str,
        nargs="+",
        default=["top-interview-150", "leetcode-75"],
        help="Slugs of the study plans to fetch",
    )

    args = parser.parse_args()

    main(args.csrf_token, args.leetcode_session, args.plans)
