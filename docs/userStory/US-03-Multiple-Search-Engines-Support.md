# US-03: Multiple Search Engines Inclusion Support

## Description

**As a** security researcher collecting domain email addresses,
**I want** to be able to specify a comma-separated list of multiple search engines using the `-e` (or `--engine`) flag,
**So that** I can dynamically select a precise subset of engines to query simultaneously, rather than being forced to use only one engine or explicitly querying 'all' minus exclusions.

## Acceptance Criteria

- **Given** the user runs the CLI tool,
- **When** they provide a comma-separated list of plugins via the `-e` flag (e.g., `python3 EmailHarvester.py -d target.com -e google,bing,yahoo`),
- **Then** the tool must parse the argument, validate that all requested engines exist in the plugins directory, and execute the search across all validated engines sequentially or systematically.
- **And** the tool must compile, deduplicate, and merge the email results from all explicitly included engines.
- **And** if an invalid engine is supplied in the list, the program must gracefully notify the user of the invalid plugin and exit.

## Technical Notes

- The current implementation only supports `-e all` or `-e single_engine`.
- Refactor the conditional block handling `args.engine` to split by commas and loop through the parsed list, mirroring the string-split logic already present for the exclusion flag (`-r`).
- Maintain backward compatibility so that passing a single engine without commas still functions correctly.
