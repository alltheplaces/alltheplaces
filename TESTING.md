# TESTING

This document summarizes the testing setup and changes on 11/12/2025 made for alltheplaces.

## How to run tests.

### How run isolated testfiles

```bash
pytest <your/file/path> 
```
OR

```bash
uv run pytest <your/file/path> 
```

### How run repo-wide test

```bash
uv run pytest
```
OR 
```bash
pytest
```

## Files created/modified

### Created (Test Files)
These files were created to thest their corresponding source modules:

- tests/test_geo_me.py — tests `locations/storefinders/geo_me.py`
- tests/test_genspider.py — tests `locations/commands/genspider.py`
- tests/test_sitemap.py — tests `locations/commands/sitemap.py`
- tests/test_nsi.py — tests `locations/commands/nsi.py`
- tests/test_wp_store_locator.py — tests `locations/storefinders/wp_store_locator.py`

### Modified
These files were modified and updated.

- locations/storefinders/treeplotter.py (added comprehensive exception handling)
- pyproject.toml (added test dependencies and pytest configuration)
- uv.lock (updated lockfile after adding test dependencies)

## Description of custom exceptions and their use cases

### TreePlotterConfigError

**Definition:**
Raised when the spider is incorrectly configured (missing/invalid host, folder, or layer_name).

**Where raised:**
- start_requests()

**Why:**
To fail fast before making invalid HTTP requests.

---

### TreePlotterAPIError

**Definition:**
Raised when API responses are malformed, missing expected keys, or contain invalid structures.

**Where raised:**
- `_json()` when JSON cannot be decoded
- `_expect()` when nested keys are missing
- parse_species_list()
- parse_tree_ids() for missing pids/total/count
- parse_tree_details() for invalid feature structures

**Why:**
To clearly isolate API-shape issues and make them testable.

---

### TreePlotterDataError

**Definition:**
Raised when JSON is valid but logically inconsistent (e.g., data contradicts itself).

**Intended use:**
- PID count mismatch in parse_tree_ids
- Any future logical inconsistencies

**Note:**
Current code still raises RuntimeError for PID mismatches. Future refactor recommended.


## Test coverage summary
The following is the test coverage summary for the files modified and added as part of this project.

                                                                                                          Stmts   Miss  Cover
locations/commands/genspider.py                                                                             64      0   100%

locations/commands/sitemap.py                                                                               75      8    89%

locations/commands/nsi.py                                                                                   92      0   100%

locations/storefinders/wp_store_locator.py                                                                  101     25    75%

locations/storefinders/geo_me.py                                                                            67      1    99%

locations/storefinders/treeplotter.py                                                                       131    102    22%

TOTAL                                                                                                       110796  55654    50%


## Any known issues or limitations

Two files needed updating when running repo wide test. 
- locations/data/nsi-wikidata.json 
- tests/data/londis.html

In `locations/storefinders/treeplotter.py`:

- PID count mismatch currently raises RuntimeError instead of TreePlotterDataError.
- parse_tree_details() skips malformed features but does not raise, which is intentional.


