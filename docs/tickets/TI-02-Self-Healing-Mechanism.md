# TI-02: Self-Healing Plugin Mechanism

## Description
Improve search plugin resilience by allowing them to handle changes in search engine URL structures or HTML tags through a "Probe & Fallback" approach.

## Acceptance Criteria
- [ ] Implement a `PluginProbe` system to check if the returned search result actually contains expected markers (results count, links).
- [ ] If markers are missing, try a **fallback URL template** from a predefined list.
- [ ] Add basic "bot-human" markers detectior to distinguish between "No Results" and "Blocked/Challenge".
- [ ] Log "Healing events" to notify the user when a fallback is used.

## Context
If Google changes `search?q=%40{word}` to a different query parameter, the current plugin fails silently or returns an empty list.

## Proposed Strategy
Add a list of `backup_urls` to each plugin and a check for common result container tags (id/class) like `id="search"` for Google.
