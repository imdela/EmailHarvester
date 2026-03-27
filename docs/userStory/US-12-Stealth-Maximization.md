# US-12: Stealth Maximization (TOR & UA Rotation)

**As a** security researcher  
**I want to** bypass CAPTCHAs and engine blocking through autonomous IP and identity rotation  
**So that** I can reach high-batch targets (2000+) without being challenged or rate-limited by providers.

---

## Acceptance Criteria

1.  **TOR Proxy Integration**: Add a optional `--tor` flag to route all harvesting traffic through a local TOR SOCKS5 proxy (default: 127.0.0.1:9050).
2.  **Autonomous IP Rotation**: On detection of a `429 Rate Limit` or `PARTIAL_CAPTCHA`, the tool must trigger a **New TOR Identity (IP Shift)** using the `stem` library (Control Port 9051) and retry the batch immediately.
3.  **User-Agent Fluidity**: Integrate a randomization pool of 300+ modern browser headers (Windows, Android, MacOS, iOS) and rotate them for **every individual batch request**.
4.  **Adaptive Burst Timing**: Implement a non-linear "Burst & Rest" jitter (e.g., 5 rapid requests followed by a randomized 20s pause) to mimic human behavioral patterns.

---

## Technical Considerations

*   **Dependencies**: `stem` for TOR control and core network proxy configuration.
*   **Isolation**: Ensure UA rotation happens at the thread-level to avoid multi-thread identity collision.
