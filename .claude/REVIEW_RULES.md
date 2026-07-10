# PR Review Rules

## Quick Merge (all CI checks passing, no deeper review needed)
- **Dependabot dependency bumps** - merge if all CI checks pass
  - If the version is a release candidate (e.g. `rc1`, `rc2`), check the changelog to confirm
    whether the final stable release has since dropped with no changes - if so, treat as stable
  - If the RC contains a security fix (CVE), prefer merging promptly even without a stable release
  - **Always check the CodeBuild spider run logs for stack traces** - a passing pytest/pre-commit
    is not sufficient. A dependency bump may introduce runtime breakage (e.g. a Twisted `Context`
    API change that breaks Scrapy's `_inlineCallbacks`) that only shows up when spiders actually run.
    If all tested spiders crash with the same traceback, the bump is incompatible - do not merge.
- **pre-commit.ci autoupdate** - merge if all CI checks pass

## Dead Spider Removals (bot-generated)
- Do NOT auto-merge - first investigate whether the spider can be recovered/rewritten
- **Check PR comments first** - someone may have already investigated and left a note saying
  it's recoverable (or confirmed it's dead). If a comment says it's recoverable, do not merge.
  Check all comments including reviews - member feedback (especially `association: member`) carries
  more weight and should be respected. If a member says "don't remove yet", do not merge without
  further investigation.
- Check the PR body for the failure reason (status codes, elapsed time, run history)
- Check if the target site is still live (`curl -I <url>`)
- Common recoverable failures:
  - Sitemap regex no longer matches (e.g. trailing slash added) - fix the regex
  - Page structure changed from microformat to JSON-LD - rewrite using `StructuredDataSpider`
  - Site now requires a browser UA - add `USER_AGENT: BROWSER_DEFAULT`
  - Spider inherited from a parent that uses a different data source (e.g. Google Sheets CSV)
    but the target site itself is live - the spider needs rewriting, not deletion
  - Site is behind AWS WAF / Cloudflare - add `requires_proxy = True` and retest before deleting
  - JS variable or JSON blob the spider extracted has moved/renamed - check current page source
    and update the extraction logic
  - Spider had `requires_proxy` previously but it was dropped in a rewrite - restore it
  - Brand rebranded (URL changed, new brand name) - update spider rather than delete
- Common unrecoverable failures:
  - Site blocked by Cloudflare/Incapsula/AWS WAF **and** Zyte returns a ban (520) even with proxy
  - Site behind Vercel security checkpoint or DataDome - JavaScript challenge that proxy alone
    cannot bypass; needs Camoufox/Playwright, and even that may not work
  - Site behind Akamai bot protection returning HTML error pages even via proxy
  - Cloudflare non-interactive JS challenge (`cType: 'non-interactive'`) blocking the entire
    domain - detectable when even `robots.txt` returns a 403 with `cf-mitigated: challenge`
    header. Camoufox cannot bypass this reliably; close the PR as unrecoverable
  - Domain migrated to a corporate/landing page with no store locator (e.g. moved to Squarespace,
    or brand rebranded to wholesale-only)
  - Location pages removed from sitemap entirely (brand discontinued locations)
  - Spider already uses Camoufox/Playwright but still getting no data
  - Site returns connection refused / 4xx consistently across all Zyte proxy regions
  - Brand confirmed shutting down (e.g. retail closure announced with confirmed date)
- If unrecoverable: merge to delete the spider
- If merged by mistake but site is live: restore the spider in a new PR with the appropriate fix
- When opening a fix PR in response to a dead spider deletion PR, include `Closes #N` in the body
  to close the deletion PR automatically on merge

## PR Descriptions
- Be verbose - include enough context for someone to understand the change without reading the diff
- For new spiders: mention the data source (API endpoint, sitemap, etc.), location count, and any
  notable fields parsed (hours, coords, categories)
- For fixes: describe what was broken, what the root cause was, and what changed
- For rewrites: explain why the old approach stopped working and what the new approach does
- Always include `Closes #N` when the PR resolves an existing issue or deletion PR
- Include a brief summary of the CI output (count, warnings, any issues noted)

## Spider Fix PRs
- Verify CI checks pass (pytest + pre-commit; AWS CodeBuild run is informational)
- Check the diff size and scope - prefer small, focused changes
- Multi-file PRs are fine if all files are related (e.g. same brand family)
- **Geographic radius search truncation** — for spiders that query a store-locator API with a search radius (ISEADGG grid or similar), check whether the API silently truncates results at a round limit (50, 100, 200). If the per-cell result count can reach the cap, add a truncation guard following the pattern used in `store_locator_plus_self`, `storerocket`, `where2getit`, etc.: `if len(locations) >= 100: self.logger.error("Locations may be truncated …")`. If the cell size makes hitting the cap implausible (e.g. maximum observed count is well below the limit), this can be skipped, but note it in the review.
- **Try `USER_AGENT: BROWSER_DEFAULT` before `requires_proxy`** — when a spider returns 403
  or 405, first add `custom_settings = {"USER_AGENT": BROWSER_DEFAULT}` (from
  `locations.user_agents`). Some servers block Scrapy's default UA but have no geo-restriction
  — a browser UA fixes it at zero Zyte cost. Only escalate to `requires_proxy` if UA alone fails.
- **`requires_proxy`** - adds Zyte budget cost. Be reluctant to approve if the spider
  makes a large number of requests. Always ask: is there a proxy-free alternative?
  Exception: if the CodeBuild run shows a significantly lower location count without proxy
  than with (e.g. geo-blocked API returning partial results), proxy is justified.
- **`requires_proxy` does not work with all bot protections** - specifically:
  - **Vercel security checkpoint** - JS challenge; proxy is not enough, needs Playwright
  - **DataDome** - aggressive bot protection; even proxy + Playwright often fails
  - **Akamai bot manager** - returns HTML error pages even via proxy; needs Camoufox or rewrite
  - **Cloudflare Managed Challenge** - proxy alone may not bypass; test with CodeBuild before merging
  - If Zyte returns a 520 "Website Ban" error, proxy is definitively not working
- **`requires_proxy` + `SitemapSpider`** - `requires_proxy` routes page fetches through Zyte,
  but `SitemapSpider` fetches the sitemap and `robots.txt` via the regular downloader first.
  If those are also blocked, add `ROBOTSTXT_OBEY: False` and override `start_requests()` or
  `_parse_sitemap()` to add Zyte/proxy meta to those requests too.
- **`requires_proxy` + Playwright** - these don't always combine cleanly. Playwright requests
  go through the Playwright middleware, not the Zyte downloader. If both are needed, override
  `start_requests()` to pass `playwright=True` meta on the initial fetch, and ensure the
  sitemap/robots fetch also goes through Playwright.
- **Playwright** - not a significant cost concern (slightly slower but not expensive)
  - Before adding Playwright to a spider that hits a JSON API, check whether `requires_proxy`
    alone is sufficient - the API may return JSON directly with proxy, making Playwright
    (and its `response.xpath("//pre/text()")` pattern) unnecessary.
- **`is_playwright_spider = True`** - this is the DEPRECATED pattern. New spiders
  should subclass `PlaywrightSpider` instead. Push a fixup commit if seen.
- **Rate limiting** (`CONCURRENT_REQUESTS`, `DOWNLOAD_DELAY`) - if a spider previously
  had these and a PR removes them, ask whether the target site needs throttling.
  Restore them unless the author has a clear reason for removal.
- **`yield Feature(item)`** - double-wraps the item and is wrong; should be `yield item`.
  Push a fixup if seen.
- **Mutable shared `item_attributes` dict** - if a subclass does `item_attributes = SHARED`
  then `item_attributes["brand"] = "Other"`, it mutates the shared dict and corrupts the
  parent spider. Fix with `item_attributes = {**SHARED, "brand": "Other"}`.
- **`tycheck` failures** - check if the error is a real type issue or a runner crash/stale run.
  Common real issues and preferred fixes:
  - `spider.crawler.stats` is typed as `StatsCollector | None` - capture it at the top of the
    method with a `None` guard: `stats = spider.crawler.stats; if stats is None: return item`,
    then call `stats.inc_value(...)` throughout. Do **not** use `# ty: ignore` for this.
  - `process_item` in a pipeline should be typed `-> Feature` (it returns the item), not
    `-> Iterable[Feature]` (pipelines return, they don't yield).
  - `response.json()` on a plain `Response` type - fix with `# ty: ignore[unresolved-attribute]`
    (same pattern used elsewhere in the codebase).
- Stray/accidental comments or debug artifacts - fix in a follow-up commit

## Shared Storefinder / Infrastructure Changes
- Requires more careful review - CI does not re-run downstream spiders when
  a storefinder changes, so runtime failures won't be caught automatically
- Read the full change carefully; use LLM analysis to spot logic issues
- Key things to check:
  - Error handling: should processing stop on error? (usually yes - add `return`)
  - Pagination: does it still work correctly after the change?
  - Does any new import or helper exist and work as expected?

## New Spiders
- Verify brand/wikidata attributes are correct
- **Wikidata QID validation** — do not trust a `brand_wikidata` value just because it is syntactically valid (`Q` + digits). LLMs frequently hallucinate QIDs that exist but refer to a completely unrelated entity (e.g. a village in Nigeria assigned to a laundromat brand). Always verify the QID label matches the brand name by checking `https://www.wikidata.org/wiki/Q<id>` or searching NSI. If no real QID can be found, omit `brand_wikidata` rather than guessing.
- **Missing wikidata on large brands** — if a new spider produces a large number of locations (>100) but has no `brand_wikidata`, flag it. A brand with hundreds of locations almost certainly has a Wikidata entry. Search NSI (`grep -i "<brand>" locations/data/nsi.json`) and Wikidata before merging. If genuinely not in Wikidata, a comment explaining the search was done is acceptable.
- Check location count looks reasonable
- **Category must use `apply_category`** — never set `item["extras"]["amenity"]` (or any other tag) directly. Always use `apply_category(Categories.X, item)` from `locations.categories`. If the right `Categories` enum value doesn't exist yet, add it to `categories.py` in the same PR.
- **`add_list` for multi-value extras tags** — `apply_category` no longer accumulates values;
  calling it twice for the same key overwrites the first. For tags that genuinely need
  semicolon-separated values (e.g. `cuisine`), use `add_list(key, value, item)` from
  `locations.categories`. For `cuisine` specifically, prefer letting NSI enrichment set it
  rather than hardcoding it in the spider.
- Check `requires_proxy` is not added unnecessarily
- **Dual-function locations** — when a single location serves two distinct purposes (e.g. a car
  dealer with both sales and service), yield two separate items using `deepcopy(item)` with
  distinct ref suffixes (`f"{item['ref']}-sales"`, `f"{item['ref']}-service"`), each with its
  own `apply_category` call. Do not stack two top-level category tags on one item.
- **`"extras": Categories.X.value` in `item_attributes` is an antipattern** — `.value` returns a
  raw dict that bypasses `apply_category`'s field routing. Always call
  `apply_category(Categories.X, item)` in the parse method (or `post_process_item`) instead of
  embedding `{"extras": Categories.X.value}` in `item_attributes`. Push a fixup commit if seen.
- **`name` vs `branch`** - when `brand` is set in `item_attributes` and the source provides a per-location store name that differs from the brand (e.g. an operator's store name like `Cellular Sales Bellingham Meridian St`), that value belongs in `branch`, not `name`. The brand name from `item_attributes` will serve as the feature name.

## Data Quality - Fields
These apply to both new spiders and fixes. Sample the CI output GeoJSON before approving.

### Images
- **Images must be per-location**, not a shared brand logo or placeholder.
- Drop images whose URL contains words like `placeholder`, `default`, `logo`, `brand`, or a
  hash that is identical across all features — these are not useful.
- If `StructuredDataSpider` is passing through a bad image, pop it in `post_process_item`.
- If the source returns a **non-unique image** (same URL on multiple locations), drop it entirely.
  For single-page API responses, count occurrences with `Counter` and only emit when count == 1.
  For per-page crawls, filter by known placeholder URL substrings (e.g. `"Mountains_pattern" not in url`).
- One PR per spider for image fixes.

### Address fields
- **`addr:street` vs `addr:street_address`**: `addr:street` is the street name only (e.g. `"Main Street"`),
  `addr:street_address` is the full address line including house number (e.g. `"123 Main Street"`).
  DictParser maps a source `street` key to `addr:street` - if the value contains a house number,
  override with `street_address` instead. Store finder sites almost always provide the full address
  line, so `addr:street_address` is more common in practice.
- **`addr:state`** must be a state/province code, never a country code (e.g. `"FR"`, `"DE"`).
  If structured data sets `addressRegion` to a country code, pop `state` from the item.
- **`addr:country`** should be an ISO 3166-1 alpha-2 code (`"US"`, `"FR"`, ...), not a full name.
- **`addr:street_address`** should not contain the city, postcode, or country - those belong
  in their own fields. Flag if DictParser or structured data is collapsing the full address
  into a single field.
- Do not put `None`, empty strings, or `"null"` into address fields - omit the field entirely.

### Phone / email / website
- Fields should be **per-location**, not a single corporate value stamped on every item.
- Low-uniqueness warnings in the CodeBuild output (e.g. `Only 3 (0.50%) unique phone numbers`)
  are a signal to investigate - but for **franchise chains** where each franchisee genuinely
  shares a number (rare), this can be acceptable. Confirm by spot-checking the raw data.
- A shared website (e.g. the brand homepage) on every item is fine **only if** there is no
  per-location URL available. Prefer per-location URLs when the site provides them.

### Opening hours
- If the source provides hours data (structured data, JSON in the page, API field), **parse
  them**. Do not leave `opening_hours` empty when the data is available.
- Use `OpeningHours` from `locations.hours` and the appropriate `DAYS_XX` dict for the locale.
- **Assign the `OpeningHours` object directly** — do not call `.as_opening_hours()`. Set
  `item["opening_hours"] = oh` (not `oh.as_opening_hours()`). The pipeline accepts the object
  directly and skips an extra validation pass. Push a fixup commit if `.as_opening_hours()` is seen.
- Watch for sites that only provide **date-specific** hours (e.g. next 7 days) rather than
  recurring weekly hours - deduplicate by day-of-week using a `seen_days` set, taking the
  first occurrence of each weekday.
- `openingHoursSpecification` entries with `validFrom`/`validThrough` are date-specific and
  are ignored by `StructuredDataSpider`'s default parser - handle them manually.
- Normalise non-standard time formats (e.g. `"8.00"` -> `"08:00"`, `"800"` -> `"08:00"`) before
  passing to `add_range`.

### Coordinates
- Items without coordinates are acceptable **only when the data is otherwise valuable** — rich address, phone, email, hours data for a brand with no other source. Use judgment: 137 international language schools with full address/contact data is worth having; a handful of locations with address-only is not.
- **Flag** any spider that yields items with `None` lat/lon — make a conscious decision rather than letting it slip through unnoticed.
- If the source returns `0` / `0.0` for lat/lon (a common placeholder for "no data"), the
  pipeline automatically drops them via the null-island check (`fabs(lat) < 3 and fabs(lon) < 3`)
  and records an `atp/geometry/null_island` stat. No spider-level filtering needed.
- **Do not use Google Maps as a coordinate source.** Following `maps.app.goo.gl` short links
  and extracting `/@lat,lon` from the redirect URL constitutes using Google data. If the only
  coordinate source on a site is a Google Maps link, accept the spider without coordinates
  rather than deriving them from Google.

### `ref` field
- Should be a **stable, unique** identifier from the source (store ID, slug, etc.).
- Do not use sequential integers generated by the spider - these will change between runs.

## CI Run Interpretation
- **`timeout`** is not a failure - the 2-minute CI limit is short. Check that the partial
  results look correct (fields populated, coordinates present, hours parsed).
- **Stale CI on old branches** - a PR that is hundreds of commits behind master may show CI
  failures that have nothing to do with its own changes (e.g. a `test_item_attributes` failure
  for a spider added to master after the PR branched). Rebase the branch onto master before
  judging whether CI failures are real.
- **`success` with warnings** - read the warning details. Low phone/email uniqueness may be
  a false alarm for franchise chains; low location counts compared to a prior run need
  investigation.
- **`success` with 0 results** - always a bug. Do not merge.
- **`no output`** - equivalent to 0 results. Always investigate before merging. Check the log
  for the failure mode: 429/403/520 (bot blocking), empty response, exception, etc.
  - A common cause is `robotstxt/forbidden: 1` in the stats - the spider's target URL is
    disallowed by robots.txt. Fix by adding `custom_settings = {"ROBOTSTXT_OBEY": False}`.
  - Another cause is `robots.txt` timing out (e.g. on an API subdomain that has no robots.txt),
    which also prevents the spider from starting. Same fix.
- **CodeBuild `fail` with a stale result** - a force-push or new commit may trigger a new
  CodeBuild run. If the latest comment shows good results but the status still shows `fail`,
  verify which build ID the status refers to. Merge once the most recent run passes.
- **Zyte 520 "Website Ban"** - means proxy is definitively not working for that site.
  `requires_proxy` alone is not a fix in this case.
- Always spot-check the output GeoJSON (or the map link) before approving a new spider.

## Automated NSI Update PRs
- The bot periodically opens PRs to sync `locations/data/nsi.json` from upstream.
- If a manual NSI fix has been merged recently (e.g. a brand rebrand), the automated PR
  may **revert** it because upstream NSI hasn't been updated yet.
- Always diff against the current master NSI before merging an automated NSI update.
  If it reverts a recent intentional change, **close the PR** with a note explaining why.
- Check `git log --oneline master | grep -i nsi` to quickly surface recent manual NSI changes
  before diffing the automated PR.

## Spider Regressions (count collapses)
- When a spider drops from thousands of results to near-zero between runs, investigate before
  assuming the spider is broken:
  1. Check if the spider previously had `requires_proxy` that was dropped in a rewrite
  2. Check if the target site's page structure changed (inspect the HTML/JSON response)
  3. Check if the site added bot protection (Akamai, Cloudflare, Vercel, DataDome)
  4. Check if the API endpoint moved or was removed entirely
- For sitemaps returning `.xml.gz` files: Scrapy's `SitemapSpider` handles gzip natively,
  so a `.xml.gz` sitemap is not itself a bug.
- A spider returning 4 results where 4600 are expected is almost certainly bot-blocked,
  not a parse error - the few results that slip through are from requests that got lucky.

## Draft PRs
- Skip entirely - do not review or merge draft PRs
- **Generic phone numbers, emails, and websites** must not be set in `item_attributes` or
  applied uniformly to every location. These appear as warnings in the AWS CodeBuild run output
  (e.g. `atp/field/phone/generic`, `atp/field/email/generic`, `atp/field/website/generic`).
- A value is "generic" if it belongs to the brand's head office or corporate website rather
  than the individual location - e.g. a single national phone number stamped on every branch.
- If you see these warnings in the CodeBuild run stats, request that the author remove the
  offending field (or fetch it per-location if it's genuinely location-specific).
- Examples of what to flag:
  - `item_attributes = {..., "phone": "+1-800-555-0100"}` - corporate number, remove it
  - `item["website"] = "https://example.com"` set unconditionally - use a per-location URL
  - `item["email"] = "info@example.com"` applied to all items - remove unless location-specific

## Issue Triage
- **Automated dead spider issues** are filed repeatedly for the same spider - close duplicates,
  keeping the newest. Reference the older issue number in the close comment (e.g. "Duplicate of #XXXX").
- **Issues with an open PR that references them** (`Closes #N` or `Fixes #N` in the PR body) -
  do NOT close manually. GitHub will close the issue automatically when the PR merges. Manually
  closing it early breaks the automation and severs the PR↔issue link.
- **Issues resolved by a merged PR** - do not close manually; they will close automatically
  when the fixing PR is merged (use `Fixes #N` in the PR body).
- **Issues where the spider was deleted** - close with a reference to the deletion PR.
- **Issues where the spider already exists (merged)** - close with a reference to the PR that
  added the spider (e.g. "We have a spider for this: `brand_xx`, added in #NNNN."). If there
  is no PR (spider was added in a direct commit), use the commit SHA instead.
- **Issues where the spider was renamed/rewritten** - close with a reference to the PR,
  noting the new spider name.
- **Stale issues** - close with a brief explanation (e.g. "API now returns clean data",
  "unable to reproduce", "upstream data issue outside spider control").
- **'Brand shutting down' issues** - only open once a confirmed closure date is known.
  Close vague ones with a note asking to reopen when a date is confirmed.
- **Duplicate location issues** - if the duplication is in the upstream data source (not a
  spider logic bug), close as an upstream data issue outside spider control.
- **Issues about data quality in an existing spider** — before filing a fix, verify the bug
  still exists in the **latest CI run output** at
  `https://alltheplaces-data.openaddresses.io/runs/2026-06-06-13-32-18/output/<spider>.geojson`.
  If already fixed, close the issue citing the PR that fixed it. If still present, fix the spider
  and open a PR with `Closes #N`. One PR per spider.
- **Verifying a bug** — before closing as "already fixed", check the latest run output GeoJSON,
  not just the spider source code (the code may have been rewritten to avoid the bug path but
  the root cause could still appear via DictParser or a storefinder base class).
- **Leaving an issue open** — when you investigate but can't fix it (e.g. site unreachable,
  needs broader architectural decision), add a comment explaining what you found.
  Do **not** post a comment saying "Investigated: ...". Just state what you found.
  Do **not** add a timestamp to the comment — GitHub adds one automatically.
- **🤖 emoji goes at the start of bot-posted comments**, not the end.
  E.g. `🤖 Spider is unrecoverable due to Cloudflare blocking.`
- **Before closing an issue as "already fixed"**, confirm the fix actually produced data by
  checking the scraper-bot CI comment on the fixing PR for item counts. A merged PR is not
  sufficient evidence — the spider may still produce 0 items.

## Existing Spider Fixes — Specific Patterns
- **Generic email**: if the source API returns the same email for every location, pop it.
  Verify by checking a sample from the API: `curl ... | python3 -c "import json,sys; j=json.load(sys.stdin); print([s.get('email') for s in j[:5]])"`.
- **Generic image**: if the same image URL appears on many locations, drop it. Strategy:
  - Single-page API: use `Counter` to count occurrences; only emit when `count == 1`.
  - Per-page crawl (StructuredDataSpider): filter known placeholder URL substrings.
  - The latest CI run GeoJSON is the authoritative source — count unique images there.
- **`addr:state` duplicating `addr:country`**: happens when a country has no states and
  the source API returns the country code in the state field. Fix in the individual spider:
  `if item.get("state") == item.get("country"): item["state"] = None`.
- **Obsolete country codes**: map in the spider, e.g. `CS` (Serbia & Montenegro) → `RS`,
  `YU` (Yugoslavia) → `RS`.
- **Placeholder field values**: pop or clear fields containing known placeholders:
  - housenumber: `"n/a"`, `"N/A"`, `"0"`
  - postcode: all-zero strings like `"0000"`, `"00000"` — check with `not postcode.replace("0", "").strip()`
  - name: `"NA"` (check source data to confirm it's a placeholder, not a real store name)
- **HTML in address fields**: use `re.sub(r"<[^>]+>", " ", value).strip()` to strip tags.
- **Wrong category**: check NSI (`grep -A5 '"QN..."' locations/data/nsi.json`) to see what
  category the brand should have before changing it.
- **Global spider overlapping country-specific spider**: preferred strategy is (b) — remove
  the country-specific spider once the global spider is verified to extract fields at parity.
  Always check field-by-field before removing: hours, phone, coords, address granularity.

- **Next.js `buildId` spiders** — spiders that derive an API URL from the Next.js `buildId`
  (fetched from `/_buildManifest.js`) must guard against stale IDs: check that the API
  response has `Content-Type: application/json` before calling `response.json()`, and log an
  error if it returns HTML (a 302/redirect signals that the buildId rotated on a site redeploy).
  Affected sites include anything using `/_next/data/<buildId>/...` URL patterns.

- **Sites requiring a session cookie from the homepage**: some Laravel/PHP sites (e.g. `seventeenice-map.glico.com`) redirect all requests to an SSO login page unless a session cookie is established first by visiting the homepage. The fix is to start the spider by requesting the homepage, then follow up with the real data requests. Scrapy carries cookies across requests in the same session automatically. Test with `curl -sc /tmp/cookies.txt <homepage> -L -o /dev/null && curl -sb /tmp/cookies.txt <data-url>` to confirm the pattern before building the spider.

## Background Agent Conventions
These apply when delegating work to background implementer agents.

- **Always use git worktrees** — agents must never commit directly to the main checkout's `master` branch. Every branch must be created in a worktree:
  ```bash
  git fetch origin
  git worktree add /tmp/wt-BRANCHNAME -b BRANCHNAME origin/master
  cd /tmp/wt-BRANCHNAME
  # write/edit, test, commit only the relevant file(s)
  git push -u origin BRANCHNAME
  gh pr create --head BRANCHNAME ...
  cd /path/to/main/checkout
  git worktree remove /tmp/wt-BRANCHNAME
  ```
- **One spider per worktree** — when building multiple spiders sequentially, create and remove a fresh worktree for each. Mixing files across worktrees causes staging confusion.
- **Commit only the spider file** — do not accidentally stage unrelated untracked files. Use `git add locations/spiders/<spider>.py` explicitly.
- **`gh pr create` works; `gh issue close` / `gh issue comment` do not** — the pi approval extension blocks interactive GitHub write operations in background agent shells. Agents should:
  - Use `gh pr create` for PRs (this works fine)
  - Use `gh api repos/alltheplaces/alltheplaces/issues/NNN/comments -f body='...'` for comments
  - Use `gh api -X PATCH repos/alltheplaces/alltheplaces/issues/NNN -f state=closed` to close issues
- **Don't run long full spider crawls** — use `--set CLOSESPIDER_ITEMCOUNT=10` for verification. A full crawl of 400+ pages will time out the agent.
- **Never dispatch more than ~5-8 concurrent `pr-handler`-style agents.** A batch of 26 concurrent agents each calling `gh` exhausted the GitHub GraphQL quota (5000/hr) in one shot, then every subsequent `gh` call from any agent or the orchestrator failed with "API rate limit already exceeded" for the rest of the hour. Before dispatching a large batch, check headroom with `gh api rate_limit --jq .resources` and dispatch in waves of ~5-8, not all at once.
- **`pr-handler` must never poll or wait inline for pending CI.** If a required check (e.g. `pre-commit.ci`) is `pending`/`queued` — not failed, not passed — the agent should check once and immediately stop, reporting a `BLOCKED_ON_CI` state with the PR number. It must not loop, sleep, or spawn its own background wait-and-merge task. One agent burned ~47k tokens and 21 minutes doing exactly this while idling on a single PR. Merging `BLOCKED_ON_CI` PRs is the orchestrator's job: one centralized, backed-off sweep (`gh pr checks N` for each, spaced out) after the batch returns — not N different improvised per-agent strategies and not multiple independent polling loops (each of which can independently re-trigger the same rate limit).
- **Don't gate fixup commits on CI already being green.** Order of operations inside `pr-handler`: review code → apply fixups if warranted → check CI once → report terminal state (`MERGE`, `BLOCKED_ON_CI`, `SUPERSEDED`, `HOLD`). A CI-pending PR can and should still get a real code review and fixup commit if one is warranted.
- **Treat "superseded by another already-merged PR" as a named terminal state (`SUPERSEDED`).** If the same fix already landed via a different PR (e.g. a rebase now conflicts because master already contains an equivalent change), detect it, defer, and never close the PR unilaterally — report it to the user with the superseding PR number and a one-line diff of approach. This is a hard rule, not just contributor-PR courtesy: see [[feedback_contributor_pr_priority]].
- **Only run `pr-handler` (or any agent doing `git checkout`/`branch`/`clean`/rebase operations) against the shared main checkout when isolated with `isolation: "worktree"`.** Multiple concurrent agents operating unisolated on the same working directory can silently delete untracked files in it — this happened to two untracked files (`REVIEW_RULES.md` itself and `SESSION_PROMPT.md`) sitting at the repo root during a 26-agent unisolated batch run. See [[feedback_use_worktrees]].
- **`pr-triage` should flag PRs likely to go stale before `pr-handler` reaches them** — specifically PRs that will need an `update-branch` rebase to merge (a rebase resets required checks back to pending). Batch those separately from clean, already-green PRs so the orchestrator doesn't mix pending-CI PRs into the same wave as ready-to-merge ones.
- **Spider class naming** — the pre-commit `check-spider-naming-consistency` hook requires the class name to be the PascalCase of the spider file name. Rules:
  - Country codes at the **end** of the name are fully uppercased: `dhl_pl.py` → `DhlPLSpider`, `djh_de.py` → `DjhDESpider`.
  - Acronyms that are **not** trailing country codes are title-cased: `steiger_stiftung_aed.py` → `SteigerStiftungAedSpider` (not `AEDSpider`).
  - Names starting with a digit use English words for the leading digit only if the first component is *entirely* digits: `7_brew_us.py` → `SevenBrewUSSpider`. If the first component mixes digits and letters (e.g. `4all`), rename the file to spell it out: `four_all_gr.py` → `FourAllGRSpider`.
  - The hook will always report the exact expected class name in its error message — use that as the ground truth.
- **Do not send too many PRs at once** — pre-commit.ci has a queue and gets overwhelmed if many PRs are opened simultaneously. Pace new spider PRs in batches of ~5 and wait for CI to clear before sending more.

## Hard Stops — Do NOT Merge When:
- A **MEMBER has posted review comments within the last 24 hours** and they haven't been resolved
  or acknowledged. GitHub's `COMMENTED` review state does NOT indicate approval — you must read
  the comment bodies. If comments are substantive objections, hold and flag for the author.
- The most recent CI run ended in **`exception` status**. An exception means the spider crashed
  mid-run; it is not the same as a timeout. Investigate the log before merging.
- **CI results across recent runs are wildly inconsistent** (e.g. 0 items → 3356 → 240 → 34919) —
  this signals a fragile spider or unreliable data source. Stabilize before merging.
- The PR **modifies shared infrastructure** (`locations/categories.py`, storefinders, pipelines)
  AND there are unresolved inline review comments from members on those files.
- A **generic field warning** (`Only 1 (0.00%) unique phone/email numbers`) appears in CI output
  and the field is being set uniformly from non-location-specific data — remove it first.

## General
- **Always read all PR comments and reviews before making a merge decision.** Member feedback
  (`association: member`) carries particular weight. If a member has raised concerns, address
  them or escalate rather than merging over the objection.
- Prefer leaving a review comment over silently fixing, UNLESS:
  - The fix is trivial (1-3 lines) and non-controversial
  - The PR author has maintainer-edit enabled (check `maintainerCanModify`)
  - In that case, push a fixup commit and note it in a comment
- When pushing a fixup commit to a fork branch:
  1. `git fetch origin pull/<N>/head:<local-branch>`
  2. Make the change, commit with a clear message
  3. `git push git@github.com:<fork-owner>/alltheplaces.git <local>:<remote-branch>`
  4. Return to master: `git checkout master`
  5. Leave a comment on the PR explaining what was changed and that CI will re-run before merging
  6. Include a 🤖 emoji in any PR comments posted as an LLM
- Each PR should address a single spider or a tightly related group - split unrelated fixes
  into separate PRs.
- `gh pr merge` requires an explicit method flag (`--squash`) when run non-interactively - omitting
  it causes an error. Always use `gh pr merge <N> --squash`.
- **All changes must go through a pull request — no exceptions.** Never commit directly to `master`,
  even for trivial one-line fixes. Create a branch, push it, open a PR, and merge via `gh pr merge`.
  The branch protection rule prevents force-pushes, so an accidental direct commit cannot be undone.
  If you accidentally commit to the local `master`, immediately `git reset HEAD~1` (before pushing)
  to unstage it, then re-apply the change on a new branch. Once pushed to remote `master` the damage
  is permanent.
