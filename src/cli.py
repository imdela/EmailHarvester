import argparse
import sys
from argparse import RawTextHelpFormatter

from src.core import (
    EmailHarvester,
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


def main() -> None:

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

    filename = args.filename or ""
    limit = args.limit
    engine = args.engine
    app = EmailHarvester(userAgent, args.proxy)
    plugins = app.get_plugins()

    all_emails = []
    excluded = args.exclude.split(",") if args.exclude else []

    engines_to_run = []
    if engine == "all":
        print(green("[+] Searching everywhere"))
        engines_to_run = [e for e in plugins if e not in excluded]
    else:
        engines_to_run = [e.strip() for e in engine.split(",")]
        for e in engines_to_run:
            if e not in plugins:
                print(red("[-] Search engine plugin not found: " + e))
                sys.exit(3)

    for search_engine in engines_to_run:
        all_emails += plugins[search_engine]["search"](domain, limit)
    all_emails = unique(all_emails)

    if not all_emails:
        print(red("[-] No emails found"))
        sys.exit(4)

    print(green("[+] Emails found: ") + cyan(str(len(all_emails))))

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
