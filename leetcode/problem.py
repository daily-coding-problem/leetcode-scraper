from typing import List


class Problem:
    def __init__(
        self,
        id: int,
        slug: str,
        content: str,
        difficulty: str,
        topics: List[str],
        companies: List[str],
        hints: List[str],
    ):
        self.id = id
        self.slug = slug
        self.content = content
        self.difficulty = difficulty
        self.topics = topics
        self.companies = companies
        self.hints = hints

        self.link = f"https://leetcode.com/problems/{self.slug}/"

    def to_dict(self):
        return {
            "id": self.id,
            "slug": self.slug,
            "content": self.content,
            "difficulty": self.difficulty,
            "topics": self.topics,
            "companies": self.companies,
            "hints": self.hints,
            "link": self.link,
        }

    def __repr__(self):
        return f"Problem(id={self.id}, title={self.slug}, difficulty={self.difficulty}, link: {self.link})"
