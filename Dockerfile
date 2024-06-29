# Use an official Python runtime as a parent image
FROM python:3.12-slim

# Create a non-root user
RUN useradd -m user

# Set the working directory for user
WORKDIR /home/user

# Switch to root user to install dependencies
USER root

# Install necessary dependencies
RUN apt-get update && \
    apt-get install -y \
		postgresql-client \
		postgresql-server-dev-all \
		curl \
		git \
		build-essential \
		procps \
		libssl-dev \
		zlib1g-dev \
		libbz2-dev \
		libreadline-dev \
		libsqlite3-dev \
		wget \
		llvm \
		libncurses5-dev \
		libncursesw5-dev \
		xz-utils \
		tk-dev \
		libffi-dev \
		liblzma-dev && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Switch to the non-root user user
USER user

# Install pyenv
RUN curl https://pyenv.run | bash

# Set up pyenv environment variables
ENV PATH="/home/user/.pyenv/bin:/home/user/.pyenv/shims:${PATH}"
RUN echo 'export PATH="/home/user/.pyenv/bin:$PATH"' >> /home/user/.bashrc && \
    echo 'eval "$(pyenv init --path)"' >> /home/user/.bashrc && \
    echo 'eval "$(pyenv init -)"' >> /home/user/.bashrc

# Install poetry
RUN curl -sSL https://install.python-poetry.org | python3 -

# Set up poetry environment variables
ENV PATH="/home/user/.local/bin:${PATH}"
RUN echo 'export PATH="/home/user/.local/bin:$PATH"' >> /home/user/.bashrc

# Copy only the files required for setting up Python environment to leverage layer caching
COPY .python-version /usr/src/app/.python-version

# Switch back to root user to install Python and dependencies
USER root
WORKDIR /usr/src/app

# Initialize pyenv and install Python version from .python-version
RUN eval "$(pyenv init --path)" && \
    eval "$(pyenv init -)" && \
    pyenv install $(cat .python-version) && \
    pyenv global $(cat .python-version)

# Create a virtual environment
RUN python -m venv .venv

# Upgrade pip to latest version
RUN pip install --upgrade pip

# Copy the rest of the application code
COPY . /usr/src/app
