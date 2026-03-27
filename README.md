# EmailHarvester (Modernized 2026 Fork)

`EmailHarvester` is an robust Open-Source utility designed to crawl through search engines specifically targeting public domain metadata to gather publicly indexed email addresses.

> **Note**: This fork was significantly refactored, modernized for Python 3 environments, and enhanced in **2026** while retaining the core features initially created by `@maldevel`.

---

## Legal & Ethical Use

**⚠️ Important Notice:** 
This tool is intended explicitly for:
* Educational purposes
* Authorized security audits (e.g., Red Teaming, authorized OSINT)
* Legitimate Business-To-Business (B2B) prospecting relying exclusively on publicly indexed data.

**Compliance requirements:**
* Usage must actively comply with all governing privacy and anti-spam legislation across jurisdictions you interact with (e.g., **GDPR** in the EU, **CAN-SPAM** in the USA, and equivalent local data-protection laws).
* **Strictly Prohibited Uses:** Illegal operations including but not limited to mass-spam generation, targeted phishing arrays, and unauthorized, disruptive extraction over secured endpoints are fundamentally prohibited. 
* Original algorithms, mechanisms, and framework architectures belong to `@maldevel` directly under **GNU General Public License v3 (GPLv3)**. This repository guarantees that the license terms, structure, and original credits remain firmly intact.

---

## Features
- Retrieves emails accurately from Search Engines (Google, Bing, Yahoo, Ask, Reddit, Github, Baidu, Dogpile, LinkedIn, Twitter, etc).
- Supports parsing comma-separated multiple engines simultaneously (`-e bing,google`).
- Supports blacklisting/excluding comma-separated engines (`-r linkedin,twitter`).
- Supports limiting search quantities (`-l`).
- Complete HTTP Proxy execution wrapper.
- Results exports out into `.xml` and `.txt` immediately.

---

## Installation & Setup

We highly recommend maintaining a clean context by executing `EmailHarvester` inside a Python `venv` virtual environment structure to assure no dependency namespace conflicts.

### 1. Clone the Repository
Choose either `HTTPS` or `SSH`:

```bash
# HTTPS method
git clone https://github.com/[your-fork]/EmailHarvester.git

# SSH method
git clone git@github.com:[your-fork]/EmailHarvester.git
```

Move into the project directory:
```bash
cd EmailHarvester
```

### 2. Configure Virtual Environment

Set up and initiate a modern Python virtual context and load the requirements:

```bash
# Initialize a new Virtual Environment namespace (venv)
python3 -m venv venv

# Activate and bind the venv
source venv/bin/activate

# Use Pip internally inside venv to install specific requirements
pip install -r requirements.txt
```

---

## Usage

Executing `EmailHarvester.py` prints the following Command Line argument tree:

```text
usage: EmailHarvester.py
       [-h] [-d DOMAIN]
       [-s FILE]
       [-e ENGINE]
       [-l LIMIT]
       [-u USER-AGENT]
       [-x PROXY]
       [--noprint]
       [-r EXCLUDED_PLUGINS]
       [-p]

options:
  -h, --help
    show this help message and exit
  -d, --domain DOMAIN
    Domain to search.
  -s, --save FILE
    Save the results into a TXT and XML file (both).
  -e, --engine ENGINE
    Select search engine plugin explicitly, supports multiple (eg. '-e google,bing,ask').
  -l, --limit LIMIT
    Limit the number of results per request structure.
  -u, --user-agent USER-AGENT
    Set a custom User-Agent networking request header.
  -x, --proxy PROXY
    Setup proxy server binding safely (eg. '-x http://127.0.0.1:8080')
  --noprint
    Silent operations; Tell EmailHarvester not to print explicit results to stdout during scanning.
  -r, --exclude EXCLUDED_PLUGINS
    Plugins to globally exclude when you default engine choice to 'all' (eg. '-r google,twitter')
  -p, --list-plugins
    List all available functional plugins in the repository explicitly.
```

### Examples 

**Search using explicit plugins exclusively (US-03 Feature):**
```bash
python3 EmailHarvester.py -d test.com -e google,bing,yahoo -l 50
```

**Search everywhere EXCEPT specified plugins:**
```bash
python3 EmailHarvester.py -d test.com -e all -r linkedin,twitter -l 500
```

---
**License / Credits**
- GNU GPLv3
- `EmailHarvester` original authored logic explicitly by `@maldevel`.