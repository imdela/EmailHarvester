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

app_emailharvester: Any = None


def search(domain: str, limit: Any) -> list[str]:
    """
    Performs Instagram searching by aggregating results from Bing and Google.
    """
    all_emails = []

    bing_url = "http://www.bing.com/search?q=site%3Ainstagram.com+%40{word}&count=50&first={counter}"
    app_emailharvester.init_search(bing_url, domain, limit, 0, 50, "Instagram [Bing]")
    app_emailharvester.process()
    all_emails.extend(app_emailharvester.get_emails())

    google_url = 'https://www.google.com/search?num=100&start={counter}&hl=en&q=site%3Ainstagram.com+"%40{word}"'
    app_emailharvester.init_search(google_url, domain, limit, 0, 100, "Instagram [Google]")
    app_emailharvester.process()
    all_emails.extend(app_emailharvester.get_emails())

    return all_emails


class Plugin:
    def __init__(self, app: Any, conf: dict[str, Any]) -> None:
        app.register_plugin("instagram", {"search": search})
        global app_emailharvester
        app_emailharvester = app
