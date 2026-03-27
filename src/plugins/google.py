"""
Plugin explicitly built to interface natively with the email harvester 'google' engine.
"""

from typing import Any

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


app_emailharvester: Any = None


def search(domain: str, limit: Any) -> list[str]:
    """
    Executes the search and harvest sequence for this specific engine.

    Args:
        domain (str): The target domain to harvest email addresses for.
        limit (Any): The maximum number of search result pages/items to parse.

    Returns:
        list[str]: A list of harvested email addresses.
    """
    url = 'https://www.google.com/search?num=100&start={counter}&hl=en&q="%40{word}"'
    app_emailharvester.init_search(url, domain, limit, 0, 100, "Google")
    app_emailharvester.process()
    return list(app_emailharvester.get_emails())


class Plugin:
    def __init__(self, app: Any, conf: dict[str, Any]) -> None:

        app.register_plugin("google", {"search": search})
        global app_emailharvester
        app_emailharvester = app
