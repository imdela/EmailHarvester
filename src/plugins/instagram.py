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

Plugin explicitly built to interface natively using Bing and Google site-search for Instagram.
"""

from typing import Any


def search(domain: str, limit: int, harvester: Any) -> list[str]:
    """Executes the search and harvest sequence for Instagram via Bing and Google.

    Args:
        domain: The target domain to harvest email addresses for.
        limit: The maximum number of search result pages/items to parse per engine.
        harvester: The EmailHarvester instance to use for processing.

    Returns:
        A aggregated list of harvested email addresses.
    """
    all_emails = []

    bing_url = "http://www.bing.com/search?q=site%3Ainstagram.com+%40{word}&count=50&first={counter}"
    harvester.init_search(bing_url, domain, limit, 0, 50, "Instagram [Bing]")
    harvester.process()
    all_emails.extend(harvester.get_emails())

    google_url = 'https://www.google.com/search?num=100&start={counter}&hl=en&q=site%3Ainstagram.com+"%40{word}"'
    harvester.init_search(google_url, domain, limit, 0, 100, "Instagram [Google]")
    harvester.process()
    all_emails.extend(harvester.get_emails())

    return all_emails


class Plugin:
    """Plugin bridge for searching emails on Instagram."""

    def __init__(self, app: Any, _conf: dict[str, Any]) -> None:
        """Initializes the plugin and registers its search method.

        Args:
            app: The parent EmailHarvester orchestrator to register with.
            _conf: Configuration dictionary containing User-Agent and proxy settings.
        """
        app.register_plugin("instagram", {"search": search})
