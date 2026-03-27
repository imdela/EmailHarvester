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

import argparse
import sys
import threading
from argparse import RawTextHelpFormatter
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TaskProgressColumn,
    TextColumn,
    TimeRemainingColumn,
)

from src.core import (
    EmailHarvester,
    EmailHarvesterError,
    ForbiddenError,
    RateLimitError,
    SearchBlockedError,
    __version__,
    checkDomain,
    checkProxyUrl,
    cyan,
    green,
    limit_type,
    red,
    unique,
    yellow,
)


def run_engine_thread(
    search_engine: str,
    domain: str,
    limit: int,
    userAgent: str,
    proxy: Any,
    tor: bool,
    progress: Any,
    save_callback: Any = None,
    deep_scraping: bool = False,
) -> tuple[list[str], str]:
    """
    Worker function to execute a single search engine sequentially within a thread.

    Args:
        search_engine (str): Name of the search engine plugin to run.
        domain (str): The target domain to harvest email addresses from.
        limit (int): The maximum number of results to fetch.
        userAgent (str): The User-Agent string to use for HTTP requests.
        proxy (Any): Parsed proxy URL configuration, if any.
        tor (bool): Flag indicating whether TOR proxy routing is active.
        progress (Any): Rich Progress bar instance for UI updates.
        save_callback (Any, optional): Callback function for stream-to-disk persistence.

    Returns:
        tuple[list[str], str]: A tuple containing the list of harvested emails and the final exit status.
    """
    # Create thread-local EmailHarvester instance to isolate instance state
    thread_app = EmailHarvester(userAgent, proxy, tor_enabled=tor)
    thread_app.save_callback = save_callback
    thread_app.deep_scraping = deep_scraping

    task_id = progress.add_task(f"[cyan]Searching in {search_engine}...", total=limit)
    thread_app.progress_callback = progress.update
    thread_app.task_id = task_id

    emails = thread_app.get_plugins()[search_engine]["search"](domain, limit)

    progress.update(task_id, completed=limit)
    return list(emails), str(thread_app.status)


def main() -> None:
    """
    Main entry point for the EmailHarvester CLI.
    Parses arguments, orchestrates plugin threads, and aggregates execution metrics.
    """
    parser = argparse.ArgumentParser(
        description=r"""

 _____                   _  _   _   _                                _              
|  ___|                 (_)| | | | | |                              | |             
| |__  _ __ ___    __ _  _ | | | |_| |  __ _  _ __ __   __ ___  ___ | |_  ___  _ __ 
|  __|| '_ ` _ \  / _` || || | |  _  | / _` || '__|\ \ / // _ \/ __|| __|/ _ \| '__|
| |___| | | | | || (_| || || | | | | || (_| || |    \ V /|  __/\__ \| |_|  __/| |   
\____/|_| |_| |_| \__,_||_||_| \_| |_/ \__,_||_|     \_/  \___||___/ \__|\___||_| 

    A tool to retrieve Domain email addresses from Search Engines | @maldevel
                                {}: {}
""".format(red("Version"), yellow(__version__)),
        formatter_class=RawTextHelpFormatter,
    )

    parser.add_argument(
        "-d",
        "--domain",
        action="store",
        metavar="DOMAIN",
        dest="domain",
        default=None,
        type=checkDomain,
        help="Domain to search.",
    )
    parser.add_argument(
        "-s",
        "--save",
        action="store",
        metavar="FILE",
        dest="filename",
        default=None,
        type=str,
        help="Save the results into a TXT and XML file (both).",
    )

    parser.add_argument(
        "-e",
        "--engine",
        action="store",
        metavar="ENGINE",
        dest="engine",
        default="all",
        type=str,
        help="Select search engine plugin(eg. '-e google').",
    )

    parser.add_argument(
        "-l",
        "--limit",
        action="store",
        metavar="LIMIT",
        dest="limit",
        type=limit_type,
        default=100,
        help="Limit the number of results.",
    )
    parser.add_argument(
        "-u",
        "--user-agent",
        action="store",
        metavar="USER-AGENT",
        dest="uagent",
        type=str,
        help="Set the User-Agent request header.",
    )
    parser.add_argument(
        "-x",
        "--proxy",
        action="store",
        metavar="PROXY",
        dest="proxy",
        default=None,
        type=checkProxyUrl,
        help="Setup proxy server (eg. '-x http://127.0.0.1:8080')",
    )
    parser.add_argument(
        "--tor",
        action="store_true",
        dest="tor",
        default=False,
        help="Enable TOR proxy (127.0.0.1:9050) and automatic identity rotation on blocks.",
    )
    parser.add_argument(
        "--noprint",
        action="store_true",
        default=False,
        help="EmailHarvester will print discovered emails to terminal. It is possible to tell EmailHarvester not to print results to terminal with this option.",
    )
    parser.add_argument(
        "-r",
        "--exclude",
        action="store",
        metavar="EXCLUDED_PLUGINS",
        dest="exclude",
        type=str,
        default=None,
        help="Plugins to exclude when you choose 'all' for search engine (eg. '-r google,twitter')",
    )
    parser.add_argument(
        "-p",
        "--list-plugins",
        action="store_true",
        dest="listplugins",
        default=False,
        help="List all available plugins.",
    )
    parser.add_argument(
        "--deep",
        action="store_true",
        dest="deep",
        default=False,
        help="Enable deep-scraping: visit discovered links recursively to find more emails (TI-01).",
    )

    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit()

    args = parser.parse_args()

    if args.listplugins:
        import pkgutil

        import src.plugins

        print(green("[+] Available plugins"))
        for _, modname, _ in pkgutil.iter_modules(src.plugins.__path__):
            print(green("[+] Plugin: ") + cyan(modname))
        sys.exit(1)

    if not args.domain:
        print(red("[-] Please specify a domain name to search."))
        sys.exit(2)
    domain = args.domain

    userAgent = args.uagent or "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:40.0) Gecko/20100101 Firefox/40.1"

    print(green("[+] User-Agent in use: ") + cyan(userAgent))

    if args.proxy:
        print(green("[+] Proxy server in use: ") + cyan(args.proxy.scheme + "://" + args.proxy.netloc))
    if args.tor:
        print(green("[+] TOR proxy enabled (127.0.0.1:9050)"))

    filename = args.filename or ""
    limit = args.limit
    engine = args.engine

    # Persistent Writing State (US-13)
    file_lock = threading.Lock()
    global_emails: set[str] = set()  # Keep track of emails already written to file

    def save_email_callback(new_emails: list[str]) -> None:
        if not filename:
            return

        with file_lock:
            with open(f"{filename}.txt", "a") as f:
                for email in new_emails:
                    if email not in global_emails:
                        f.write(email + "\n")
                        global_emails.add(email)
            # Ensure real-time flush
            # f.flush() and closing handles this in the context manager

    all_emails = []
    excluded = args.exclude.split(",") if args.exclude else []

    plugins = EmailHarvester(userAgent, args.proxy, tor_enabled=args.tor).get_plugins()
    engines_to_run = []
    if engine == "all":
        print(green("[+] Searching everywhere"))
        engines_to_run = [e for e in plugins if e not in excluded]
    else:
        engines_to_run = [e.strip() for e in engine.split(",")]
        for e in engines_to_run:
            # Check against original loaded plugins keys
            if e not in plugins:
                print(red("[-] Search engine plugin not found: " + e))
                sys.exit(3)

    final_emails = []
    engine_stats: list[tuple[str, int, str]] = []
    failed_engines: list[str] = []

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        TimeRemainingColumn(),
    ) as progress:
        # Limit concurrency to 20 threads to ensure "Network Stealth" and avoid ISP-level flagging
        max_concurrency = min(len(engines_to_run), 20)
        with ThreadPoolExecutor(max_workers=max_concurrency) as executor:
            future_to_engine = {
                executor.submit(
                    run_engine_thread,
                    engine_name,
                    domain,
                    limit,
                    userAgent,
                    args.proxy,
                    args.tor,
                    progress,
                    save_email_callback,
                    args.deep,
                ): engine_name
                for engine_name in engines_to_run
            }

            for future in as_completed(future_to_engine):
                engine_name = future_to_engine[future]
                try:
                    res, status = future.result()
                    final_emails.extend(res)
                    engine_stats.append((engine_name, len(res), status))
                except RateLimitError as e:
                    progress.console.print(yellow(f"[~] Rate limit hit for '{engine_name}': {e}"))
                    engine_stats.append((engine_name, 0, "FAILED_RATE_LIMIT"))
                except SearchBlockedError as e:
                    progress.console.print(yellow(f"[~] Captcha block in '{engine_name}': {e}"))
                    engine_stats.append((engine_name, 0, "PARTIAL_CAPTCHA"))
                except ForbiddenError as e:
                    progress.console.print(red(f"[-] Access forbidden to '{engine_name}': {e}"))
                    failed_engines.append(engine_name)
                    engine_stats.append((engine_name, 0, "FAILED_FORBIDDEN"))
                except EmailHarvesterError as e:
                    progress.console.print(red(f"[-] Error in thread '{engine_name}': {e}"))
                    failed_engines.append(engine_name)
                    engine_stats.append((engine_name, 0, "FAILED"))
                except Exception as e:
                    progress.console.print(red(f"[-] Fatal unknown error in thread '{engine_name}': {e}"))
                    failed_engines.append(engine_name)
                    engine_stats.append((engine_name, 0, "FATAL_ERROR"))

    all_emails = unique(final_emails)

    # 1. Diagnostic Report Header
    print(green("\n[+] Search Engine Diagnostics:"))
    for engine_name, count, status in sorted(engine_stats):
        symbol = green("[+]") if status == "SUCCESS" else yellow("[?]") if "PARTIAL" in status else red("[X]")
        status_colored = green(status) if status == "SUCCESS" else yellow(status)
        print(f"{symbol} {engine_name.capitalize()}: {cyan(str(count))} emails ({status_colored})")

    if failed_engines:
        print(red(f"\n[-] The following engines hit fatal internal errors: {', '.join(failed_engines)}"))

    if not all_emails:
        print(red("\n[-] No emails found"))
        sys.exit(4)

    print(green("\n[+] Total unique emails found: ") + cyan(str(len(all_emails))))
    if filename:
        print(green("[+] Total unique emails saved to: ") + cyan(f"{filename}.txt"))

    if not args.noprint:
        for emails in all_emails:
            print(emails)

    if filename:
        try:
            print(green("[+] Saving results to files"))
            with open(filename, "w") as out_file:
                for email in all_emails:
                    try:
                        out_file.write(email + "\n")
                    except Exception as email_err:
                        print(red("[-] Exception writing {}: {}".format(email, email_err)))
        except Exception as e:
            print(red("[-] Error saving TXT file: " + str(e)))

        try:
            filename = filename.split(".")[0] + ".xml"
            with open(filename, "w") as out_file:
                out_file.write('<?xml version="1.0" encoding="UTF-8"?><EmailHarvester>')
                for email in all_emails:
                    out_file.write("<email>{}</email>".format(email))
                out_file.write("</EmailHarvester>")
            print(green("[+] Files saved"))
        except Exception as er:
            print(red("[-] Error saving XML file: " + str(er)))
