# Guide for AI coding agents

Read this before writing or changing a spider. Reviewers reject spiders that don't follow it.
The goal is the **smallest spider that is correct**: a typical one is 20-40 lines.
Most of what a new spider needs is already done by a pipeline, a base class or a helper.

Start from the closest file in [`templates/spiders/`](templates/spiders) and from a similar, recently
merged spider. Don't copy older spiders blindly: many predate the helpers below.

## Don't re-implement what the pipelines do

See [`docs/PIPELINES.md`](docs/PIPELINES.md). Spiders emit raw values and the pipelines clean them.

- **Duplicates**: `DuplicatesPipeline` drops repeated `ref`s. Never keep a `seen_*`/`emitted_*` set
  or an `if ref in ...` guard. Just make `ref` the source's stable unique id.
- **Phones, emails, URL schemes, country codes, whitespace**: no regexes, no `tel:`/`mailto:` stripping,
  no `.strip()` on every field, no hardcoded `country` when the spider name ends in a country code.
- **Dropped fields**: use `drop_attributes = {"phone"}` (a set) for a source field that's known to be junk.
- **Brand fields**: put `brand`, `brand_wikidata` and a static `name` in the class-level `item_attributes`.

## Use the shared helpers

- Pick the simplest base class: `JSONBlobSpider`, `StructuredDataSpider` (+ `SitemapSpider`/`CrawlSpider`),
  or a class in `locations/storefinders/` if the site runs a known locator platform.
- `DictParser.parse(obj)` instead of copying fields one at a time. Set `name_is_branch = True` on
  `JSONBlobSpider`/`StructuredDataSpider` instead of `item["branch"] = item.pop("name")`.
- Subclassing a `locations/storefinders/` class: read its `parse()` first and don't re-set what it or `DictParser` already
  fills in (`ref`, `phone`, `postcode`, `website`). In `post_process_feature` only add what is brand-specific.
- Categories: `apply_category(Categories.X, item)`. Never write `item["extras"]["shop"]` or
  `item_attributes["extras"] = Categories.X.value`. Grep `locations/categories.py` for an existing entry before adding one.
- Sources with a sitemap or JSON-LD: prefer `SitemapSpider` + `StructuredDataSpider` (`wanted_types = [...]` to filter) over bespoke crawling.
- Opening hours: `OpeningHours` from `locations/hours.py`. Assign the object itself: `item["opening_hours"] = oh`
  (no `.as_opening_hours()`); for 24/7 use `add_days_range(DAYS, "00:00", "23:59")`. Use `add_range`/`add_days_range` for structured data,
  `add_ranges_from_string` only for free text. Take day names from `DAYS_*` and `sanitise_day`; never write a local weekday dict (including for French/other languages, or a "closed" word map).
  Pass `time_format=` for 12-hour times, listing only the formats the source uses.
  Call `set_closed(day)` for days the source marks closed.
- Joining address parts: `merge_address_lines([...])` from `locations/pipelines/address_clean_up.py`.
- Radius-only APIs: `country_iseadgg_centroids`. Reuse `map_payment` and the other shared tables in `categories.py`.
- Run `uv run pytest tests/test_item_attributes.py -q` to check `brand` strings against NSI.

## Keep the code small

- No tiny single-purpose helper methods (`parse_hours` wrapping one call, `make_request`). Inline them.
- Comments: none by default. One line only where the *why* is non-obvious. No docstrings on `parse`.
- No per-spider test files. No logging or stats unless something needs them.
- No defensive code for impossible cases (`.get(k) or {}`, `or ""`, `try/except` around `.index()`, `isinstance` checks on
  fixed JSON). Use `feature["key"]`, not `.get("key")`, for keys that always exist; if the source breaks the assumption the
  spider should fail loudly. Test every line: "what happens if I delete this?" If nothing, delete it.
- Don't add custom stats, counters or empty-result checks unless they're needed (a result-cap guard on a radius API is the exception); pipelines already emit `atp/field/*` stats.
- No string cleaners (zero-width chars, `str(x).removesuffix(".0")`, regexes on phone): `CleanStringsPipeline` and friends do it.
- Avoid a `seen_*` set even for overlapping radius/bbox/postcode searches. It's slightly more efficient, but every LLM then copies it.
- Don't build query strings with `urlencode` in class attributes; write the URL literal or build requests in `start`.
- Don't change throttling (`DOWNLOAD_DELAY`, `AUTOTHROTTLE_*`, `RETRY_*`), `ALLOWED_LOW_DOWNLOAD_DELAY`, or add Playwright/proxy
  "just in case". Weekly runs have hours; CI timeouts aren't a reason. Don't edit `tests/` or its allow-lists to make CI pass.
- English identifiers and comments, even for non-English sources.
- Don't add `requires_proxy` unless the site really blocks datacenter IPs (it costs money).

## Data correctness

- `ref` is a stable id from the source, never an enumerate index.
- Verify `brand_wikidata` by reading the Wikidata page. Models hallucinate QIDs. If you can't verify it, omit it.
- Check the store-finder domain really belongs to the brand, and that the chain still operates.
  Chains with fewer than ~10 locations usually aren't worth a spider.
- Don't geocode via Google or follow shortlinks to extract coordinates. Reading `lat,lon` from a `maps.google.com/?q=lat,lon`
  link the site itself publishes is fine. Otherwise leave coordinates unset rather than invent them. If they look swapped, swap them.
- Prefer the brand's own site or API over aggregators and third-party locator sites.
- Don't break addresses down below `street_address`/`housenumber`/`street` by regex, and don't use `branch` for something
  that isn't a branch name (maybe `operator`). Don't regex a combined name into brand and branch.
- Only use well-established OSM tags. Check taginfo before adding a `Categories` entry; don't invent tags, don't add
  unused entries, and don't double-tag.
- `brand`/`brand_wikidata` should match NSI. If the brand isn't in NSI, ask whether it's a brand at all (not a network,
  collective or aggregator) before setting it. Never reuse a deleted QID.
- Sanity-check counts and meaning against OSM: a suspiciously large or round count, or a category that doesn't match what
  the business does (e.g. truck dealers tagged `shop=truck`).
- Never use a `disused:` prefix; use `end_date` or `set_closed()`.
- Language suffixes on tags are ISO 639-1 codes (`branch:ja`, `name:en`), never country codes (`jp`). For amenities use
  `Extras.*` with `apply_yes_no` rather than raw tag strings; sockets in Japan are `socket:nema_1_15`.
- Read a few output records, not just the item count:
  `uv run scrapy runspider locations/spiders/<name>.py -o /tmp/out.geojson -L INFO`

## Naming and PRs

- Spider file/name: `brand_name_cc` (see [`docs/SPIDER_NAMING.md`](docs/SPIDER_NAMING.md)); class names must match.
- One spider per PR. Title like `Add brand_name_us spider (500 locations)` or `[Brand] Fix spider`.
- PR description: Data source, location count, anything notable. Link issues with `Closes #N`.
  Verify every claim (e.g. "all stores were missing state") against real output or the published weekly stats before writing it.
- Check no open PR or existing spider already covers the brand, and rebase on master.
- While iterating use the HTTP cache: `uv run scrapy crawl -s HTTPCACHE_ENABLED=True -s HTTPCACHE_EXPIRATION_SECS=604800 <name>`.
- Before you finish, shrink the diff: ask yourself which lines could go. Reviewers regularly cut LLM spiders to half their size.
- Run `uv run pre-commit run --files <changed files>` before pushing.
- More detail, with reviewer precedents: [`.claude/agents/add-spider.md`](.claude/agents/add-spider.md) and
  [`.claude/REVIEW_RULES.md`](.claude/REVIEW_RULES.md).
