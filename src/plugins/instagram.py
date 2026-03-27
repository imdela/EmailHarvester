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
    """Executes the search and harvest sequence for Instagram.

    Retrieves configurations from the harvester's centralized YAML registry.
    """
    configs = harvester.get_plugin_config("instagram")
    for config in configs:
        harvester.init_search(
            config["url"],
            domain,
            limit,
            config["counter_init"],
            config["counter_step"],
            config["name"],
        )
        harvester.process()
    return list(harvester.get_emails())


class Plugin:
    """Plugin bridge for searching emails on Instagram."""

    def __init__(self, app: Any, _conf: dict[str, Any]) -> None:
        """Initializes the plugin and registers its search method."""
        app.register_plugin("instagram", {"search": search})
