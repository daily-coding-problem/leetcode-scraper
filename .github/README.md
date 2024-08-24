# LeetCode Scraper [![Python Tests](https://github.com/daily-coding-problem/leetcode-scraper/actions/workflows/python-pytests.yml/badge.svg)](https://github.com/daily-coding-problem/leetcode-scraper/actions/workflows/python-pytests.yml)

![Docker](https://img.shields.io/badge/-Docker-2496ED?style=flat-square&logo=Docker&logoColor=white)
![Linux](https://img.shields.io/badge/-Linux-FCC624?style=flat-square&logo=linux&logoColor=black)
![Python](https://img.shields.io/badge/-Python-3776AB?style=flat-square&logo=python&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/-PostgreSQL-336791?style=flat-square&logo=postgresql&logoColor=white)

LeetCode Scraper is a Python-based tool designed to fetch and store details from LeetCode study plans into a PostgreSQL database. This tool leverages Docker for easy setup and environment management.

## Table of Contents

- [Features](#features)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
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
git clone --recurse-submodules https://github.com/daily-coding-problem/leetcode-scraper.git
cd leetcode-scraper
```

**Setup Python Environment**

Use the following commands to set up the Python environment if you do not want to use Docker:

```sh
python -m venv .venv
source .venv/bin/activate
pip install poetry
poetry install --no-root
```

**Setup Docker**

If you would like to use Docker, ensure Docker and Docker Compose are installed on your machine. If not, follow the installation guides for [Docker](https://docs.docker.com/get-docker/) and [Docker Compose](https://docs.docker.com/compose/install/).

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

Run the scraper with the specified company and timeframe:

```sh
docker compose run leetcode-scraper --company google --timeframe 3m
```

Or without Docker:

```sh
poetry run python main.py --company google --timeframe 3m
```

This will fetch the most asked questions at Google in the last 3 months.

The options for `--timeframe` are: `30d`, `3m`, or `6m`.
- If no timeframe is specified, the default is `6m`.
- If the timeframe is invalid, the default will be used.

## Running Tests

Run the tests with the following command:

```sh
poetry run pytest
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
