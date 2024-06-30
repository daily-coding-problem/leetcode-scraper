# LeetCode Scraper [![Python Tests](https://github.com/daily-coding-problem/leetcode-scraper/actions/workflows/python-pytests.yml/badge.svg)](https://github.com/daily-coding-problem/leetcode-scraper/actions/workflows/python-pytests.yml)

LeetCode Scraper is a Python-based tool designed to fetch and store details from LeetCode study plans into a PostgreSQL database. This tool leverages Docker for easy setup and environment management.

## Table of Contents

- [Features](#features)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Project Structure](#project-structure)
- [License](#license)

## Features

- Fetches LeetCode problems and study plans
- Stores data in a PostgreSQL database
- Provides caching to reduce redundant requests
- Handles rate limiting with retry mechanisms

## Prerequisites

Before you begin, ensure you have met the following requirements:

- Docker and Docker Compose installed on your machine.
- Python 3.12 or higher.
- [PostgreSQL database](https://github.com/daily-coding-problem/database).

## Installation

**Clone the Repository**

```sh
git clone https://github.com/your-username/leetcode-scraper.git
cd leetcode-scraper
```

**Setup Docker**

   Ensure Docker and Docker Compose are installed on your machine. If not, follow the installation guides for [Docker](https://docs.docker.com/get-docker/) and [Docker Compose](https://docs.docker.com/compose/install/).

**Build Docker Images**

```sh
docker compose build
```

**Create the Network**

```sh
docker network create dcp
```

## Configuration

**Environment Variables**

Create a `.env` file in the project root with the following content:

```env
# LeetCode credentials
CSRF_TOKEN=your_csrf_token
LEETCODE_SESSION=your_leetcode_session

# PostgreSQL credentials
POSTGRES_USER=your_db_user
POSTGRES_PASSWORD=your_db_password
POSTGRES_DB=your_db_name
POSTGRES_PORT=5432
```

## Usage

Run the scraper with the specified plans:

```sh
docker compose run leetcode-scraper --plans leetcode-75 top-interview-150
```

Or without Docker:

```sh
poetry run python main.py --plans leetcode-75 top-interview-150
```

## Running Tests

Run the tests with the following command:

```sh
poetry run pytest
```

## Project Structure

```
leetcode-scraper/
├── database/
│   ├── __init__.py
│   ├── database.py
├── leetcode/
│   ├── __init__.py
│   ├── leetcode.py
│   ├── client.py
│   ├── problem.py
│   ├── study_plan.py
├── tests/
│   ├── __init__.py
│   ├── test_database.py
│   ├── test_leetcode.py
├── scripts/
│   ├── entrypoint.sh
├── .env
├── docker-compose.yml
├── Dockerfile
├── main.py
├── pyproject.toml
├── README.md
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
