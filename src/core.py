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
import re
import sys
import time
from sys import platform as _platform
from typing import Any
from urllib.parse import urlparse

import requests
import validators
from termcolor import colored

################################


if _platform == "win32":
    import colorama

    colorama.init()


class MyParser:
    def __init__(self) -> None:
        """
        Initializes the parsing buffer.
        """
        self.temp: list[str] = []
        self.results: str = ""
        self.word: str = ""

    def extract(self, results: str, word: str) -> None:
        """
        Loads the raw HTML text and the target search word into the parser.

        Args:
            results (str): The raw HTML or text corpus containing potential emails.
            word (str): The domain suffix (e.g., '@github.com') to search for.
        """
        self.results = results
        self.word = word

    def genericClean(self) -> None:
        for e in (
            "<KW> </KW> </a> <b> </b> </div> <em> </em> <p> </span>\n"
            "                    <strong> </strong> <title> <wbr> </wbr>".split()
        ):
            self.results = self.results.replace(e, "")
        for e in "%2f %3a %3A %3C %3D & / : ; < = > \\".split():
            self.results = self.results.replace(e, " ")

    def emails(self) -> list[str]:
        self.genericClean()
        reg_emails = re.compile(r"[a-zA-Z0-9.\-_+#~!$&\',;=:]+" + r"@" + r"[a-zA-Z0-9.-]*" + self.word)
        self.temp = reg_emails.findall(self.results)
        emails = self.unique()
        return emails

    def unique(self) -> list[str]:
        self.new = list(set(self.temp))
        return self.new


###################################################################


class EmailHarvester:
    def __init__(self, userAgent: str, proxy: Any) -> None:
        """
        Initializes the EmailHarvester engine and dynamically loads search plugins.

        Args:
            userAgent (str): The HTTP user-agent string used for native web requests.
            proxy (Any): An optional parsed proxy configuration URL object.
        """
        self.plugins: dict[str, Any] = {}
        self.proxy = proxy
        self.userAgent = userAgent
        self.parser = MyParser()
        self.activeEngine = "None"
        plugins: dict[str, Any] = {}
        import src.plugins

        for _importer, modname, _ispkg in pkgutil.iter_modules(src.plugins.__path__):
            mod = importlib.import_module(f"src.plugins.{modname}")
            if hasattr(mod, "Plugin"):
                plugins[modname] = mod.Plugin(self, {"useragent": userAgent, "proxy": proxy})

    def register_plugin(self, search_method: str, functions: dict[str, Any]) -> None:
        self.plugins[search_method] = functions

    def get_plugins(self) -> dict[str, Any]:
        return self.plugins

    def show_message(self, msg: str) -> None:
        print(green(msg))

    def init_search(
        self, url: str, word: str, limit: str | int, counterInit: str | int, counterStep: str | int, engineName: str
    ) -> None:
        """
        Configures the scraping constraints and limits for a specific plugin run.

        Args:
            url (str): The paginated URL structure belonging to the target plugin.
            word (str): The target domain to harvest explicitly.
            limit (str | int): Maximum total result pages to query natively.
            counterInit (str | int): Starting offset parameter for pagination.
            counterStep (str | int): Step size to increment pagination natively.
            engineName (str): String identifier belonging to the current executor plugin.
        """
        self.results = ""
        self.totalresults = ""
        self.limit = int(limit)
        self.counter = int(counterInit)
        self.url = url
        self.step = int(counterStep)
        self.word = word
        self.activeEngine = engineName

    def do_search(self) -> None:
        """
        Executes the network request bridging the explicitly formulated plugin URL.

        Raises:
            SystemExit: Invoked natively if the network request fails fatally (Exit code 4).
        """
        try:
            urly = self.url.format(counter=str(self.counter), word=self.word)
            headers = {"User-Agent": self.userAgent}
            if self.proxy:
                proxies = {self.proxy.scheme: "http://" + self.proxy.netloc}
                r = requests.get(urly, headers=headers, proxies=proxies)
            else:
                r = requests.get(urly, headers=headers)

        except Exception as e:
            print(e)
            sys.exit(4)

        if r.encoding is None:
            r.encoding = "UTF-8"

        self.results = r.content.decode(r.encoding)
        self.totalresults += self.results

    def process(self) -> None:
        while self.counter < self.limit:
            self.do_search()
            time.sleep(1)
            self.counter += self.step
            print(
                green("[+] Searching in {}:".format(self.activeEngine)) + cyan(" {} results".format(str(self.counter)))
            )

    def get_emails(self) -> list[str]:
        self.parser.extract(self.totalresults, self.word)
        return self.parser.emails()


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
    url_checked = urlparse(url)
    if (url_checked.scheme not in ("http", "https")) | (url_checked.netloc == ""):
        raise argparse.ArgumentTypeError("Invalid {} Proxy URL (example: http://127.0.0.1:8080).".format(url))
    return url_checked


def limit_type(x: str) -> int:
    x_int = int(x)
    if x_int > 0:
        return x_int
    raise argparse.ArgumentTypeError("Minimum results limit is 1.")


def checkDomain(value: str) -> str:
    domain_checked = validators.domain(value)
    if not domain_checked:
        raise argparse.ArgumentTypeError("Invalid {} domain.".format(value))
    return value


###################################################################
