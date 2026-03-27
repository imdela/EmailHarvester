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

Plugin explicitly built to interface natively with the email harvester 'ask' engine.
"""

from typing import Any


def search(domain: str, limit: int, harvester: Any) -> list[str]:
    """Executes the search and harvest sequence for the Ask.com engine.

    Refactored to use the parent harvester's search cycle for consistent
    stealth and networking management.

    Args:
        domain: The target domain to harvest email addresses for.
        limit: The maximum number of search result pages/items to parse.
        harvester: The EmailHarvester instance to use for processing.

    Returns:
        A list of harvested email addresses.
    """
    # Ask uses page numbers (1, 2, 3...) instead of result offsets
    url = "http://www.ask.com/web?q=%40{word}&page={counter}"
    harvester.init_search(url, domain, limit, 1, 1, "Ask")
    harvester.process()
    return list(harvester.get_emails())


class Plugin:
    """Plugin bridge for the Ask.com search engine."""

    def __init__(self, app: Any, _conf: dict[str, Any]) -> None:
        """Initializes the plugin and registers its search method.

        Args:
            app: The parent EmailHarvester orchestrator to register with.
            _conf: Configuration dictionary containing User-Agent and proxy settings.
        """
        app.register_plugin("ask", {"search": search})
