# TI-10: DuckDuckGo Lite Resilient Plugin (Rule 11)

## Description

Implement a new search engine plugin for DuckDuckGo using its "Lite" (non-JavaScript) version. This engine is specifically chosen for its high resilience to TOR-based scraping and its privacy-friendly nature, which often results in fewer blocks compared to Google or Bing. This plugin will serve as a reliable fallback in the EmailHarvester engine.

## Acceptance Criteria

- [ ] Add DuckDuckGo Lite configuration (URL, pagination) to `src/config/engines.yaml`.
- [ ] Create `src/plugins/duckduckgo.py` following the new stateless architecture.
- [ ] Ensure the plugin correctly handles DuckDuckGo Lite's specific HTML structure for result parsing.
- [ ] Add unit tests specifically for DuckDuckGo parsing logic.
- [ ] Verify functionality through TOR in a real-world test.

---
**Status:** Open
