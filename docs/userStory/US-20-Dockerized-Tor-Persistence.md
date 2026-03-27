# US-20: Dockerized TOR Proxy and Identity Rotation

## Status
- **Role**: Developer
- **Objective**: Replace local TOR service dependency with a portable, dockerized SOCKS5 proxy allowing programmatic identity rotation.

## Context
Currently, EmailHarvester fails with `PARTIAL_BLOCKED` if a local TOR service is not running on port 9050. This limits the tool's portability and ease of use in diverse environments.

## Acceptance Criteria
1. **Containerization**: A `docker-compose.yml` must be provided to orchestrate both EmailHarvester and a TOR proxy container.
2. **Proxy Choice**: Use a lightweight, maintained image (e.g., `barneybuffet/tor`) that supports ControlPort and Password authentication.
3. **Configuration**:
    - SOCKS5 Proxy on port 9050.
    - ControlPort on port 9051.
    - Password protection for the ControlPort via environment variables.
4. **Resilience**: The `stem` controller in `src/core.py` must be updated to connect to the container's network name or a configurable host.
5. **Noob-Friendly**: A single command should be sufficient to start a stealthy harvesting session.

## Implementation Details
- **Image**: `barneybuffet/tor`
- **Environment Variables**:
    - `TOR_CONTROL_PASSWORD`: `emailharvester_secret`
    - `TOR_CONTROL`: `true`
- **Network**: Bridge network to allow communication between services.

## Validation Tasks
- [ ] Run `docker-compose up`.
- [ ] Execute EmailHarvester with `--tor`.
- [ ] Verify that IP rotates successfully when a 429/Captcha is detected.
