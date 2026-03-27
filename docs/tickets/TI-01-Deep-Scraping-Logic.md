# TI-01: Deep-Scraping Logic Implementation

## Description
Extend the current `EmailHarvester` search process to not only extract emails from the search results' HTML but also to visit and scrape the URLs found in these results ("Second-Level Scraping").

## Acceptance Criteria
- [ ] Add a `LinkExtractor` method to `MyParser` to find valid outbound links in search results.
- [ ] Implement a recursive or secondary loop in `EmailHarvester.process()` to visit these links.
- [ ] Ensure second-level requests also respect TOR/Wait/Proxy constraints and rotate User-Agents.
- [ ] Limit deep-scraping depth to 1 to avoid infinite loops or excessive traffic.
- [ ] Maintain performance through multi-threading or async logic (optional but recommended).

## Technical Consideration
- Use `urlparse` and standard regex for link extraction if no heavy HTML parser like `BeautifulSoup` is added.
- Monitor for potential "Bot challenges" on target websites as well as search engines.
