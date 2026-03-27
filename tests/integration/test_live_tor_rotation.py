import time

import pytest
import requests

from src.core import EmailHarvester


@pytest.mark.integration
def test_live_tor_rotation_changes_ip() -> None:
    """
    Live Infrastructure Integration Test (US-20).
    Connects to the real TOR container (via compose.yaml) and requests an IP echo service.
    Triggers a rotation using refresh_tor_identity() and verifies that the new IP differs.
    This guarantees that the proxy infrastructure is perfectly sound without hammering search engines.
    """
    app = EmailHarvester("IntegrationTest-UA", proxy=None, tor_enabled=True)

    # Pre-flight check: if TOR control is not accessible, skip the test gracefully (no compose running)
    try:
        if not app.refresh_tor_identity():
            pytest.skip(
                "TOR container is not active or refused auth. Run 'docker compose up -d' first to test live infrastructure."
            )
    except Exception:
        pytest.skip("Could not connect to TOR container control port.")

    # Extremely lightweight IP echo service
    url = "https://api.ipify.org"
    proxies = {
        "http": f"socks5h://{app.settings.tor_host}:{app.settings.tor_port}",
        "https": f"socks5h://{app.settings.tor_host}:{app.settings.tor_port}",
    }

    try:
        r1 = requests.get(url, proxies=proxies, timeout=app.settings.timeout)
        ip1 = r1.text.strip()

        # Ordonnate a strict rotation
        success = app.refresh_tor_identity()
        assert success is True, "Failed to execute NEWNYM signal against Tor Control."

        # Give Tor sufficient time to tear down and rebuild a new proxy circuit
        time.sleep(10.0)

        # Re-fetch the IP via the same socks proxy
        r2 = requests.get(url, proxies=proxies, timeout=app.settings.timeout)
        ip2 = r2.text.strip()

        # Core assertion: the resulting IPs must fundamentally differ
        assert ip1 != ip2, f"TOR IP did not rotate upon circuit reset! (Stuck on {ip1})"

    except requests.exceptions.RequestException as e:
        pytest.fail(f"Live network test failed due to unavailable routes: {e}")
