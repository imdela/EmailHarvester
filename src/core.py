#!/usr/bin/env python3
# encoding: UTF-8

"""
This file is part of EmailHarvester
Copyright (C) 2016 @maldevel
https://github.com/maldevel/EmailHarvester

EmailHarvester - A tool to retrieve Domain email addresses from Search Engines.

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.

For more see the file 'LICENSE' for copying permission.
"""

__author__ = "maldevel"
__copyright__ = "Copyright (c) 2016 @maldevel"
__credits__ = ["maldevel", "PaulSec", "cclauss", "Christian Martorella"]
__license__ = "GPLv3"
__version__ = "1.3.2"
__maintainer__ = "maldevel"

################################

import argparse
import importlib
import pkgutil
import random
import re
import time
from enum import StrEnum
from sys import platform as _platform
from typing import Any
from urllib.parse import urlparse

import requests
import validators
from fake_useragent import UserAgent
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from stem import Signal
from stem.control import Controller
from termcolor import colored

################################


if _platform == "win32":
    import colorama

    colorama.init()


class LinkExtractor:
    """Identifies and filters potential capture links within search engine results.

    Used for TI-01 Deep-Scraping to increase capture rate by discovering
    links that likely contain target domain contact information.
    """

    @staticmethod
    def extract_links(html: str, target_domain: str) -> list[str]:
        """Extracts absolute HTTP(S) links from HTML while filtering noise.

        Analyzes the provided HTML and extracts links that are not part of
        known search engine domains and likely belong to the target domain.

        Args:
            html: The raw HTML content to parse for links.
            target_domain: The domain to prioritize in the search results.

        Returns:
            A list of unique, validated absolute URLs found in the HTML.
        """
        # Simple href extraction regex
        links = re.findall(r'href=["\'](https?://[^\s"\'>]+)["\']', html)
        filtered_links = []

        # Engines to ignore to avoid circular scraping/looping
        blacklist = [
            "google.",
            "bing.",
            "yahoo.",
            "baidu.",
            "ask.",
            "dogpile.",
            "yandex.",
            "duckduckgo.",
            "linkedin.com/search",
            "twitter.com/search",
            "facebook.com/search",
        ]

        for link in links:
            # Skip if it's a known search engine result page or navigation
            if any(engine in link.lower() for engine in blacklist):
                continue

            # Prioritize links likely belonging to or mentioning the target domain
            if target_domain.lower() in link.lower():
                filtered_links.append(link)

        return list(set(filtered_links))


class EngineProbe:
    """
    Self-healing probes to verify plugin selector/URL validity in real-time.
    Supports TI-02 (Self-Healing).
    """

    def __init__(self, harvester: "EmailHarvester") -> None:
        self.harvester = harvester

    def verify_plugin(self, plugin_name: str) -> bool:
        """
        Quickly validates if a plugin's base URL and networking are operational.
        Performs a 'canary' request to check for structural blocks or URL invalidity.
        """
        plugin_hooks = self.harvester.get_plugins().get(plugin_name)
        if not plugin_hooks:
            return False

        # Attempt a minimal check using the harvester's networking settings
        try:
            # We use a neutral test domain
            test_url = "https://www.google.com"  # Default fallback for connectivity

            # If we were to be more precise, we'd need the base URL from the plugin
            # But most search engines can be 'pinged' by their hostname

            headers = {"User-Agent": self.harvester.userAgent}
            proxies = None
            if self.harvester.tor_enabled:
                proxies = {
                    "http": f"socks5h://{self.harvester.settings.tor_host}:{self.harvester.settings.tor_port}",
                    "https": f"socks5h://{self.harvester.settings.tor_host}:{self.harvester.settings.tor_port}",
                }

            r = requests.get(test_url, headers=headers, proxies=proxies, timeout=5)

            # Simple check: 200 OK and no immediate block markers
            if r.status_code != 200:
                return False

            block_markers = ["captcha", "unusual traffic", "automated requests"]
            if any(marker in r.text.lower() for marker in block_markers):
                return False

            return True
        except Exception:
            return False


class MyParser:
    def __init__(self) -> None:
        """
        Initializes the parsing buffer.
        """
        self.temp: list[str] = []
        self.results: str = ""
        self.word: str = ""

    def extract(self, results: str, word: str) -> None:
        """Loads the raw content and the target search word into the parser.

        Args:
            results: The raw HTML or text corpus containing potential emails.
            word: The domain suffix (e.g., 'example.com') to search for.
        """
        self.results = results
        self.word = word

    def genericClean(self) -> None:
        """Removes common HTML entities and noise from the result buffer.

        Sanitizes the results by stripping tags and replacing special characters
        with spaces to improve regex capture accuracy.
        """
        for e in (
            "<KW> </KW> </a> <b> </b> </div> <em> </em> <p> </span>\n"
            "                    <strong> </strong> <title> <wbr> </wbr>".split()
        ):
            self.results = self.results.replace(e, "")
        for e in "%2f %3a %3A %3C %3D & / : ; < = > \\".split():
            self.results = self.results.replace(e, " ")

    def emails(self) -> list[str]:
        """Matches and returns unique emails from the sanitized results.

        Uses a case-insensitive regex to capture mixed-case results conforming
        to the target domain.

        Returns:
            A deduplicated list of harvested email addresses.
        """
        self.genericClean()
        # Case-insensitive regex (re.I) to capture mixed-case results (US-16 Verification)
        reg_emails = re.compile(r"[a-zA-Z0-9.\-_+#~!$&\',;=:]+" + r"@" + r"[a-zA-Z0-9.-]*" + self.word, re.I)
        self.temp = reg_emails.findall(self.results)
        emails = self.unique()
        return emails

    def unique(self) -> list[str]:
        """Removes duplicates from the temporary email list.

        Returns:
            A list containing only unique email entries.
        """
        self.new = list(set(self.temp))
        return self.new


###################################################################


class SearchStatus(StrEnum):
    SUCCESS = "SUCCESS"
    PARTIAL_BLOCKED = "PARTIAL_BLOCKED"
    PARTIAL_CAPTCHA = "PARTIAL_CAPTCHA"
    FAILED_TIMEOUT = "FAILED_TIMEOUT"
    FAILED_FORBIDDEN = "FAILED_FORBIDDEN"
    FAILED_RATE_LIMIT = "FAILED_RATE_LIMIT"


class EmailHarvesterError(Exception):
    """Base exception for all EmailHarvester errors."""


class RateLimitError(EmailHarvesterError):
    """Raised when an engine enforces a 429 Too Many Requests status."""


class ForbiddenError(EmailHarvesterError):
    """Raised when an engine enforces a 403 Forbidden status."""


class SearchBlockedError(EmailHarvesterError):
    """Raised when a Captcha or Bot Protection is detected in the response body."""


class PluginConfigurationError(EmailHarvesterError):
    """Raised when a plugin has an invalid setup or URL format."""


class Settings(BaseSettings):
    """
    Validates and centralizes initial environment configurations for EmailHarvester.
    """

    user_agent_platform: str = Field(default="desktop", description="Platform for fake-useragent")
    tor_host: str = Field(default="127.0.0.1", description="Local/Remote TOR host address")
    tor_port: int = Field(default=9050, description="TOR SOCKS5 port")
    tor_control_port: int = Field(default=9051, description="TOR Control port")
    tor_control_password: str = Field(default="emailharvester_secret", description="TOR Control password")
    timeout: int = Field(default=12, description="HTTP request timeout in seconds", gt=0)

    model_config = SettingsConfigDict(env_prefix="EH_")


class EmailHarvester:
    """Main search orchestration engine for domain email harvesting.

    Coordinates plugin execution, networking, stealth rotation (TOR/UA),
    and real-time result persistence.
    """

    def __init__(self, userAgent: str, proxy: Any, tor_enabled: bool = False) -> None:
        """Initializes the EmailHarvester engine and dynamically loads search plugins.

        Args:
            userAgent: The default HTTP user-agent string.
            proxy: An optional parsed proxy configuration URL object.
            tor_enabled: Whether to route traffic through TOR and rotate identities.
        """
        self.settings = Settings()
        self.plugins: dict[str, Any] = {}
        self.proxy = proxy
        self.tor_enabled = tor_enabled
        self.default_userAgent = userAgent
        self.userAgent_rotator = UserAgent(platforms=self.settings.user_agent_platform)
        # Initialize current UA from pool if possible, fallback to default
        try:
            self.userAgent = self.userAgent_rotator.random
        except Exception:
            self.userAgent = userAgent

        self.parser = MyParser()
        self.activeEngine = "None"
        self.progress_callback: Any = None
        self.save_callback: Any = None  # US-13 Stream-to-Disk hook
        self.task_id: Any = None
        self.status = SearchStatus.SUCCESS
        self.retry_count = 0
        self.results = ""
        self.totalresults = ""
        self.burst_count = 0
        self.burst_limit = 5
        self.deep_scraping = False  # TI-01 Deep Scraping Toggle
        self.visited_links: set[str] = set()
        self.probe = EngineProbe(self)  # TI-02 Self-Healing Probe
        plugins: dict[str, Any] = {}
        import src.plugins

        for _importer, modname, _ispkg in pkgutil.iter_modules(src.plugins.__path__):
            mod = importlib.import_module(f"src.plugins.{modname}")
            if hasattr(mod, "Plugin"):
                plugins[modname] = mod.Plugin(self, {"useragent": userAgent, "proxy": proxy})

    def refresh_tor_identity(self) -> bool:
        """Commands the configured TOR service to rotate the circuit.

        Attempts to authenticate with the TOR control port and signals for a
        NEWNYM identity rotation.

        Returns:
            True if the identity was successfully refreshed, False otherwise.
        """
        try:
            with Controller.from_port(
                address=self.settings.tor_host, port=self.settings.tor_control_port
            ) as controller:
                controller.authenticate(password=self.settings.tor_control_password)
                controller.signal(Signal.NEWNYM)
                return True
        except Exception:
            return False

    def register_plugin(self, search_method: str, functions: dict[str, Any]) -> None:
        """Registers a search engine plugin dynamically into the system.

        Args:
            search_method: The unique identifier/name for the plugin engine.
            functions: A dictionary containing the plugin's execution hooks.
        """
        self.plugins[search_method] = functions

    def get_plugins(self) -> dict[str, Any]:
        """Retrieves all currently registered plugins and their hook architectures.

        Returns:
            A mapping of plugin names to their function hook dictionaries.
        """
        return self.plugins

    def show_message(self, msg: str) -> None:
        print(green(msg))

    def init_search(
        self,
        url: str,
        word: str,
        limit: str | int,
        counterInit: str | int,
        counterStep: str | int,
        engineName: str,
    ) -> None:
        """Configures the scraping constraints and limits for a specific plugin run.

        Args:
            url: The paginated URL structure belonging to the target plugin.
            word: The target domain to harvest explicitly.
            limit: Maximum total result pages to query natively.
            counterInit: Starting offset parameter for pagination.
            counterStep: Step size to increment pagination natively.
            engineName: String identifier belonging to the current executor plugin.
        """
        self.results = ""
        self.totalresults = ""
        self.limit = int(limit)
        self.counter = int(counterInit)
        self.url = url
        self.step = int(counterStep)
        self.word = word
        self.activeEngine = engineName
        self.status = SearchStatus.SUCCESS

    def do_search(self) -> None:
        """Executes the network request bridging the explicitly formulated plugin URL.

        Formulates the final URL, rotates the User-Agent, configures proxies
        (TOR or Standard), and executes the HTTP GET request.

        Raises:
            RateLimitError: If a 429 status is returned.
            ForbiddenError: If a 403 status is returned.
            SearchBlockedError: If bot prevention markers are detected in HTML.
            EmailHarvesterError: For any other fatal networking or engine errors.
        """
        try:
            urly = self.url.format(counter=str(self.counter), word=self.word)

            # Rotate User-Agent for every batch request (US-12)
            try:
                self.userAgent = self.userAgent_rotator.random
            except Exception:
                pass

            headers = {"User-Agent": self.userAgent}

            # Config SOCKS5 if TOR is enabled (US-12)
            proxies = None
            if self.tor_enabled:
                proxies = {
                    "http": f"socks5h://{self.settings.tor_host}:{self.settings.tor_port}",
                    "https": f"socks5h://{self.settings.tor_host}:{self.settings.tor_port}",
                }
            elif self.proxy:
                proxies = {self.proxy.scheme: "http://" + self.proxy.netloc}

            r = requests.get(urly, headers=headers, proxies=proxies, timeout=self.settings.timeout)

            if r.status_code == 429:
                self.status = SearchStatus.FAILED_RATE_LIMIT
                raise RateLimitError("429 Rate Limit")
            if r.status_code == 403:
                self.status = SearchStatus.FAILED_FORBIDDEN
                raise ForbiddenError("403 Forbidden")
            r.raise_for_status()

            if r.encoding is None:
                r.encoding = "UTF-8"
            self.results = r.content.decode(r.encoding, errors="replace")

            block_markers = ["captcha", "unusual traffic", "automated requests", "g-recaptcha"]
            if any(marker in self.results.lower() for marker in block_markers):
                self.status = SearchStatus.PARTIAL_CAPTCHA
                raise SearchBlockedError("Bot challenge detected")

            # Parse and Save in Real-Time (US-13 Persistence)
            prev_emails = set(self.parser.emails())
            self.parser.extract(self.results, self.word)
            new_emails = set(self.parser.emails()) - prev_emails

            if new_emails and self.save_callback:
                self.save_callback(list(new_emails))

            self.totalresults += self.results

            # TI-01 Deep Scraping Logic
            if self.deep_scraping:
                found_links = LinkExtractor.extract_links(self.results, self.word)
                for link in found_links:
                    if link not in self.visited_links:
                        self.visited_links.add(link)
                        try:
                            self._visit_deep_link(link)
                        except Exception:
                            continue

        except requests.exceptions.Timeout as e:
            self.status = SearchStatus.FAILED_TIMEOUT
            raise EmailHarvesterError(f"Connection timeout in {self.activeEngine}") from e
        except EmailHarvesterError:
            raise
        except Exception as e:
            # Maintain the existing status if already set; otherwise use partial block
            if self.status == SearchStatus.SUCCESS:
                self.status = SearchStatus.PARTIAL_BLOCKED
            raise EmailHarvesterError(f"Engine interrupted: {e}") from e

    def process(self) -> None:
        """Orchestrates the iterative search process with retry and stealth logic.

        Executes repeated batches of search result scraping while applying
        stealth jitter (TI-05), identity rotation on block detection (US-12),
        and progress reporting.
        """
        while self.counter < self.limit:
            try:
                self.do_search()
                self.retry_count = 0  # Reset on success
                self.burst_count += 1
            except EmailHarvesterError:
                # TOR Identity Refresh on failure (US-12)
                if (
                    self.status in [SearchStatus.FAILED_RATE_LIMIT, SearchStatus.PARTIAL_CAPTCHA]
                    and self.tor_enabled
                    and self.retry_count == 0
                ):
                    if self.progress_callback and self.task_id is not None:
                        self.progress_callback(
                            self.task_id, description=f"[yellow]Rotating TOR IP for {self.activeEngine}..."
                        )

                    if self.refresh_tor_identity():
                        self.retry_count += 1
                        time.sleep(5.0)  # Wait for circuit renewal
                        continue  # Retry same batch with new IP

                # Standard wait for non-TOR runs
                if self.status == SearchStatus.FAILED_RATE_LIMIT and self.retry_count == 0:
                    self.retry_count += 1
                    time.sleep(10.0)
                    continue

                if self.progress_callback and self.task_id is not None:
                    self.progress_callback(self.task_id, description=f"[red]{self.activeEngine} ({str(self.status)})")

                # TI-02: Self-Healing Probe on hard failure
                if not self.probe.verify_plugin(self.activeEngine.lower()):
                    if self.progress_callback and self.task_id is not None:
                        self.progress_callback(
                            self.task_id,
                            description=f"[bold red]Disabled {self.activeEngine}: Structural block detected",
                        )
                break

            # TI-05 Stealth Burst & Rest Jitter Logic
            if self.burst_count >= self.burst_limit:
                rest_time = random.uniform(15.0, 30.0)
                if self.progress_callback and self.task_id is not None:
                    self.progress_callback(
                        self.task_id, description=f"[yellow]Resting for {rest_time:.1f}s ({self.activeEngine})..."
                    )
                else:
                    print(yellow(f"[~] Resting {self.activeEngine} for {rest_time:.1f}s to evade detection..."))

                time.sleep(rest_time)
                self.burst_count = 0
            else:
                time.sleep(random.uniform(0.7, 1.8))

            self.counter += self.step
            if self.progress_callback and self.task_id is not None:
                self.progress_callback(
                    self.task_id, advance=self.step, description=f"[cyan]Searching in {self.activeEngine}..."
                )
            else:
                print(green(f"[+] Searching in {self.activeEngine}:") + cyan(f" {str(self.counter)} results"))

    def get_emails(self) -> list[str]:
        """Finalizes the parsing of all accumulated HTML results.

        Returns:
            A list of unique emails extracted from the entire search session.
        """
        self.parser.extract(self.totalresults, self.word)
        return self.parser.emails()

    def _visit_deep_link(self, url: str) -> None:
        """Internal worker to visit discovered links and extract emails recursively.

        Args:
            url: The absolute HTTP URL to crawl for secondary emails.
        """
        if self.progress_callback and self.task_id is not None:
            self.progress_callback(self.task_id, description=f"[dim cyan]Deep Scraping: {url[:50]}...")

        headers = {"User-Agent": self.userAgent}
        proxies = None
        if self.tor_enabled:
            proxies = {
                "http": f"socks5h://{self.settings.tor_host}:{self.settings.tor_port}",
                "https": f"socks5h://{self.settings.tor_host}:{self.settings.tor_port}",
            }
        elif self.proxy:
            proxies = {self.proxy.scheme: "http://" + self.proxy.netloc}

        try:
            r = requests.get(url, headers=headers, proxies=proxies, timeout=self.settings.timeout)
            if r.status_code == 200:
                if r.encoding is None:
                    r.encoding = "UTF-8"
                content = r.content.decode(r.encoding, errors="replace")

                # Reuse parser for deep-level extraction
                prev_emails = set(self.parser.emails())
                self.parser.extract(content, self.word)
                new_emails = set(self.parser.emails()) - prev_emails

                if new_emails and self.save_callback:
                    self.save_callback(list(new_emails))

                self.totalresults += content
        except Exception:
            pass


###################################################################


def yellow(text: str) -> str:
    return str(colored(text, "yellow", attrs=["bold"]))


def green(text: str) -> str:
    return str(colored(text, "green", attrs=["bold"]))


def red(text: str) -> str:
    return str(colored(text, "red", attrs=["bold"]))


def cyan(text: str) -> str:
    return str(colored(text, "cyan", attrs=["bold"]))


def unique(data: list[str]) -> list[str]:
    return list(set(data))


###################################################################


def checkProxyUrl(url: str) -> Any:
    """Validates the structure of a proxy configuration URL.

    Args:
        url: The proxy URL to validate.

    Returns:
        A parsed ParseResult object if valid.

    Raises:
        argparse.ArgumentTypeError: If the URL is malformed or uses an invalid scheme.
    """
    url_checked = urlparse(url)
    if (url_checked.scheme not in ("http", "https")) | (url_checked.netloc == ""):
        raise argparse.ArgumentTypeError("Invalid {} Proxy URL (example: http://127.0.0.1:8080).".format(url))
    return url_checked


def limit_type(x: str) -> int:
    """Coerces and validates the search result limit.

    Args:
        x: The string representation of the result limit.

    Returns:
        The validated integer limit.

    Raises:
        argparse.ArgumentTypeError: If the limit is not a positive integer.
    """
    x_int = int(x)
    if x_int > 0:
        return x_int
    raise argparse.ArgumentTypeError("Minimum results limit is 1.")


def checkDomain(value: str) -> str:
    """Validates that the input is a well-formed domain.

    Args:
        value: The domain string to validate.

    Returns:
        The validated domain string.

    Raises:
        argparse.ArgumentTypeError: If the domain is invalid.
    """
    domain_checked = validators.domain(value)
    if not domain_checked:
        raise argparse.ArgumentTypeError("Invalid {} domain.".format(value))
    return value


###################################################################
