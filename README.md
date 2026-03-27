# EmailHarvester (Modernized 2026 Powerhouse)

`EmailHarvester` is a high-performance OSINT utility designed to retrieve domain email addresses from global search engines using concurrent orchestration, stealth rotation, and resilient data accumulation.

> **Note**: This fork was significantly refactored in **2026** to implement multi-threaded engine execution, TOR identity rotation, and stream-to-disk persistence while retaining the core GPLv3 logic by `@maldevel`.

---

## 🚀 Key Modernized Features (2026)

- **⚡ Multi-Threaded Orchestration**: Runs all search engines concurrently (up to 20 threads) for 10x faster harvesting.
- **🕵️ Stealth Maximization**: Autonomous **TOR Identity Rotation** (`--tor`) and per-batch **User-Agent Pool** randomization.
- **💾 Atomic Persistence**: Emails are streamed to disk (`-s`) in real-time. If the tool crashes at 90%, your results are already safe.
- **🛡️ Resilience**: Heuristic detection of CAPTCHAs and "Bot Challenges" with automated 429 rate-limit retries.
- **📊 Diagnostic Reporting**: Professional per-engine success/partial/failure dashboard.

---

## Legal & Ethical Use

**⚠️ Important Notice:** 
This tool is intended for authorized security audits, OSINT research, and educational purposes. Usage must strictly comply with **GDPR**, **CAN-SPAM**, and local data protection laws. Mass-spamming or unauthorized scraping of secured endpoints is forbidden.

---

## Installation & Setup

```bash
# 1. Clone & Enter
git clone https://github.com/imdela/EmailHarvester.git && cd EmailHarvester

# 2. Setup Venv & Dependencies
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# 3. (Optional) Setup TOR for Stealth
sudo apt install tor
# Ensure ControlPort 9051 and CookieAuthentication are setup in /etc/tor/torrc
```

---

## Usage

```text
usage: EmailHarvester.py [-h] [-d DOMAIN] [-s FILE] [-e ENGINE] [-l LIMIT]
                         [-u USER-AGENT] [-x PROXY] [--tor] [--noprint]
                         [-r EXCLUDE] [-p]

options:
  -d, --domain      Target domain (e.g., payoneer.com)
  -s, --save        Output filename (saves as FILE.txt). Streams in real-time.
  -e, --engine      explicit engines (google, bing, all, etc)
  -l, --limit       Total result limit per engine
  -x, --proxy       HTTP/HTTPS proxy (e.g. http://127.0.0.1:8080)
  --tor             Enable TOR SOCKS5 proxy and IP rotation on blocks
  -r, --exclude     Exclude specific plugins from 'all'
  -p, --list        List all functional plugins
```

### Examples

**High-Performance Stealth Run (TOR + 2000 Batch Limit):**
```bash
python3 EmailHarvester.py -d test.com -e all -l 2000 --tor -s results_test
```

---

## Development & Testing

The project maintains a 100% test-green policy with strict static analysis:
```bash
# Static Analysis
ruff format src/ && mypy src/ --strict

# Full Test Suite (15+ Tests)
python3 -m unittest discover tests -v
```

---
**License / Credits**
- GNU GPLv3
- Original author: `@maldevel`
