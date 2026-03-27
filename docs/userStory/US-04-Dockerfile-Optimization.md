# US-04: Dockerfile Containerization and Build Optimization

## Description

**As a** DevOps engineer or user looking to run the tool in an isolated container,
**I want** the Dockerfile to reliably build the application using the local fork's context and a properly scoped virtual environment,
**So that** the deployment is fast, stable, and strictly utilizes the refactored code rather than pulling the outdated upstream repository.

## Acceptance Criteria

- **Given** the user runs `docker build`,
- **When** the Docker engine processes the Dockerfile,
- **Then** the build process should copy the local directory context directly into the image rather than issuing a `git clone` targeting the upstream repository.
- **And** the Python virtual environment (`venv`) must be properly initiated and the actual `pip install` commands must be executed using the virtual environment's executable path explicitly, ensuring dependencies are scoped correctly across Docker layers.
- **And** the `ENTRYPOINT` must utilize the virtual environment's Python binary (`/path/to/venv/bin/python`) to execute `EmailHarvester.py`.

## Technical Notes

- Replace `RUN git clone https://github.com/maldevel/EmailHarvester.git` with `COPY . /EmailHarvester`.
- Link the `RUN` commands for the virtual environment using direct bin paths (e.g., `RUN /path/to/venv/bin/pip install -r requirements.txt`).
- Clean up unused or redundant package dependencies in the `apk add` chain (such as `py3-requests` if pip installs `requests` independently via `requirements.txt`).
