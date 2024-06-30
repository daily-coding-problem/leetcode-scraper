import requests


# Experimental: CSRF token can be obtained automatically.
def get_csrf_cookie(session_id: str) -> str:
    response = requests.get(
        "https://leetcode.com/", cookies={"LEETCODE_SESSION": session_id}
    )

    if "csrftoken" not in response.cookies:
        raise Exception("CSRF token not found in cookies")

    return response.cookies["csrftoken"]
