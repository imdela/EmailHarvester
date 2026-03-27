"""
Resilience and Stealth Orchestration for EmailHarvester.
Handles IP health tracking, shared circuit pooling, and human behavior orchestration.
"""

import csv
import os
import random
import threading
import time
from datetime import datetime, timedelta
from enum import StrEnum
from typing import Any

import requests
import yaml
from stem import Signal
from stem.control import Controller
from termcolor import colored


class ThreatLevel(StrEnum):
    """Enumeration of possible IP health and usage states."""

    USING = "USING"
    REJECTED = "REJECTED"
    BLACKLISTED = "BLACKLISTED"


class ResilienceManager:
    """Centralized manager for shared scraping resilience and stealth pooling."""

    # Shared state across all instances (threads)
    _lock = threading.Lock()
    _shared_ip_cache: dict[str, dict[str, Any]] = {}
    _shared_burst_count: int = 0
    _config: dict[str, Any] = {}

    def __init__(
        self,
        storage_path: str,
        tor_enabled: bool = False,
        tor_host: str = "127.0.0.1",
        tor_port: int = 9050,
        tor_control_port: int = 9051,
        tor_password: str = "",
    ) -> None:
        self.storage_path = storage_path
        self.tor_enabled = tor_enabled
        self.settings = {
            "host": tor_host,
            "port": tor_port,
            "control_port": tor_control_port,
            "password": tor_password,
        }
        self._load_config()
        self._load_cache()

    def _load_config(self) -> None:
        """Loads stealth parameters from YAML configuration."""
        config_path = os.path.join(os.path.dirname(__file__), "config", "stealth.yaml")
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                ResilienceManager._config = yaml.safe_load(f)
        except Exception as e:
            print(colored(f"[-] Warning: Using hardcoded defaults, config load failed: {e}", "yellow"))
            # Fallback defaults if file missing
            ResilienceManager._config = {
                "timing": {"min_jitter_ms": 100, "max_jitter_ms": 500, "start_progressive_delay_s": 3},
                "burst": {"threshold_requests": 6, "pause_duration_s": 20},
                "resilience": {"quarantine_duration_min": 60, "rotation_stabilization_s": 15},
            }

    def _load_cache(self) -> None:
        """Loads IP health data into the shared cache from CSV file."""
        if not os.path.exists(self.storage_path):
            return
        with ResilienceManager._lock:
            if ResilienceManager._shared_ip_cache:
                return  # Already loaded by another thread
            try:
                with open(self.storage_path, mode="r", encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        ResilienceManager._shared_ip_cache[row["ip"]] = {
                            "status": row["status"],
                            "timestamp": datetime.fromisoformat(row["timestamp"]),
                            "reason": row.get("reason", "unknown"),
                            "attempts": int(row.get("attempts", 1)),
                        }
            except Exception as e:
                print(colored(f"[-] Error loading IP cache: {e}", "red"))

    def save_cache(self) -> None:
        """Persists shared IP health data to CSV file."""
        os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
        with ResilienceManager._lock:
            try:
                with open(self.storage_path, mode="w", encoding="utf-8", newline="") as f:
                    writer = csv.DictWriter(f, fieldnames=["ip", "status", "timestamp", "reason", "attempts"])
                    writer.writeheader()
                    for ip, data in ResilienceManager._shared_ip_cache.items():
                        # We don't persist 'USING' state to disk
                        if data["status"] == ThreatLevel.USING:
                            continue
                        writer.writerow(
                            {
                                "ip": ip,
                                "status": data["status"],
                                "timestamp": data["timestamp"].isoformat(),
                                "reason": data.get("reason", "unknown"),
                                "attempts": data.get("attempts", 1),
                            }
                        )
            except Exception as e:
                print(colored(f"[-] Error saving IP cache: {e}", "red"))

    def get_current_ip(self) -> str:
        """Fetches the current external IP address via TOR or direct connection."""
        proxies = None
        if self.tor_enabled:
            proxies = {
                "http": f"socks5h://{self.settings['host']}:{self.settings['port']}",
                "https": f"socks5h://{self.settings['host']}:{self.settings['port']}",
            }

        urls = ["https://api.ipify.org", "https://ident.me", "https://ifconfig.me/ip"]
        for url in urls:
            try:
                r = requests.get(url, proxies=proxies, timeout=10)
                if r.status_code == 200:
                    return r.text.strip()
            except Exception:
                continue
        return "unknown"

    def rotate_identity(self) -> bool:
        """Commands TOR to rotate the circuit and waits for stabilization."""
        if not self.tor_enabled:
            return False

        wait_time = self._config.get("resilience", {}).get("rotation_stabilization_s", 15)
        print(colored(f"[*] Requesting new TOR identity (Cooldown: {wait_time}s)...", "yellow"))
        try:
            with Controller.from_port(address=self.settings["host"], port=self.settings["control_port"]) as controller:
                controller.authenticate(password=self.settings["password"])
                controller.signal(Signal.NEWNYM)
                time.sleep(wait_time)
                return True
        except Exception as e:
            print(colored(f"[-] TOR rotation failed: {e}", "red"))
            return False

    def pre_flight_check(self) -> str:
        """Ensures a healthy circuit, manages state pooling, and applies jitter.

        Returns:
            The verified healthy external IP.
        """
        # 1. Staggered Start / Jitter (Humanization)
        t_conf = self._config.get("timing", {})
        jitter = random.uniform(t_conf.get("min_jitter_ms", 100), t_conf.get("max_jitter_ms", 500)) / 1000.0
        time.sleep(jitter)

        # 2. Global Burst Mode (Host Protection)
        # [FIX-1] Capture state inside the lock; sleep is applied OUTSIDE to avoid blocking all threads.
        b_conf = self._config.get("burst", {})
        burst_pause: float = 0.0
        with ResilienceManager._lock:
            ResilienceManager._shared_burst_count += 1
            if ResilienceManager._shared_burst_count >= b_conf.get("threshold_requests", 6):
                ResilienceManager._shared_burst_count = 0
                burst_pause = float(b_conf.get("pause_duration_s", 20))
        if burst_pause > 0.0:
            print(colored(f"[~] Human-like pause triggered ({burst_pause}s)...", "yellow"))
            time.sleep(burst_pause)

        # 3. IP Health & Isolation
        # [FIX-1] rotate_identity() is called OUTSIDE the lock to avoid serializing threads.
        # "unknown" is a sentinel for failed IP detection — it is never a real circuit and
        # must NOT enter the USING pool to avoid infinite retry loops.
        r_conf = self._config.get("resilience", {})
        while True:
            current_ip = self.get_current_ip()
            needs_rotate = False

            # Bypass pool management when IP detection fails — proceed without tracking.
            if current_ip == "unknown":
                return current_ip

            with ResilienceManager._lock:
                data = ResilienceManager._shared_ip_cache.get(current_ip)

                # Clean IP: Use it
                if not data:
                    ResilienceManager._shared_ip_cache[current_ip] = {
                        "status": ThreatLevel.USING,
                        "timestamp": datetime.now(),
                    }
                    return current_ip

                status = data["status"]

                # Case: Busy IP
                if status == ThreatLevel.USING:
                    print(colored(f"[!] IP {current_ip} is currently IN USE by another thread. Rotating...", "yellow"))
                    needs_rotate = True

                # Case: Blacklisted
                elif status == ThreatLevel.BLACKLISTED:
                    print(colored(f"[!] IP {current_ip} is PERMANENTLY BLACKLISTED. Rotating...", "red"))
                    needs_rotate = True

                # Case: Rejected (Quarantine)
                elif status == ThreatLevel.REJECTED:
                    quarantine_min = r_conf.get("quarantine_duration_min", 60)
                    if datetime.now() > data["timestamp"] + timedelta(minutes=quarantine_min):
                        print(colored(f"[+] IP {current_ip} finished quarantine. Re-testing...", "green"))
                        data["status"] = ThreatLevel.USING
                        return current_ip
                    print(colored(f"[!] IP {current_ip} is in QUARANTINE. Rotating...", "yellow"))
                    needs_rotate = True

            if needs_rotate:
                rotated = self.rotate_identity()
                # [FIX-2] Guard tight loop when TOR is disabled — yield CPU for 1s per retry cycle.
                if not rotated:
                    time.sleep(1.0)
                continue

            return current_ip

    def release_ip(self, ip: str) -> None:
        """Removes an IP from the pool if it was in USING status."""
        with ResilienceManager._lock:
            data = ResilienceManager._shared_ip_cache.get(ip)
            if data and data["status"] == ThreatLevel.USING:
                del ResilienceManager._shared_ip_cache[ip]

    def report_block(self, ip: str, reason: str = "unknown", permanent: bool = False, rotate: bool = True) -> None:
        """Reports a search engine block for the given IP.

        Args:
            ip: The external IP address to flag.
            reason: A human-readable description of the block cause.
            permanent: If True, the IP is marked BLACKLISTED; otherwise REJECTED.
            rotate: If True, trigger a TOR identity rotation after marking the block.
                    Set to False when the caller's retry loop already handles rotation
                    to avoid a double rotation penalty.
        """
        status = ThreatLevel.BLACKLISTED if permanent else ThreatLevel.REJECTED
        with ResilienceManager._lock:
            existing = ResilienceManager._shared_ip_cache.get(ip, {})
            attempts = existing.get("attempts", 0) + 1

            # Auto-blacklist if max attempts reached
            max_att = self._config.get("resilience", {}).get("max_attempts_before_blacklist", 5)
            if attempts >= max_att:
                status = ThreatLevel.BLACKLISTED

            ResilienceManager._shared_ip_cache[ip] = {
                "status": status,
                "timestamp": datetime.now(),
                "reason": reason,
                "attempts": attempts,
            }
        self.save_cache()
        print(colored(f"[-] IP {ip} marked as {status} (Reason: {reason}). Circuit flagged.", "red"))
        # [FIX-6] Only rotate when explicitly requested — avoids double 15s penalty
        # when the calling retry loop (e.g. process() in core.py) already handles rotation.
        if rotate:
            self.rotate_identity()
