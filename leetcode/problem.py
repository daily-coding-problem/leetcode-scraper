from typing import List


class Problem:
    def __init__(
        self,
        id: int,
        title: str,
        content: str,
        difficulty: str,
        topics: List[str],
        companies: List[str],
        hints: List[str]
    ):
        self.id = id
        self.title = title
        self.content = content
        self.difficulty = difficulty
        self.topics = topics
        self.companies = companies
        self.hints = hints

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'difficulty': self.difficulty,
            'topics': self.topics,
            'companies': self.companies,
            'hints': self.hints
        }

    def __repr__(self):
        return f"Problem(id={self.id}, title={self.title}, difficulty={self.difficulty})"

