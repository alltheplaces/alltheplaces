import json
import re
from collections import Counter, defaultdict
from math import ceil
from typing import Any, AsyncIterator, Iterable
from urllib.parse import parse_qsl

from scrapy import Request, Spider
from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines


class AdeccoSitecoreSpider(Spider):
    """
    Adecco's national sites on www.adecco.com are Sitecore sites sharing one branch search API. This class contains
    their common spider code.

    `site_name`, `language` and `root_path_id` (the item ID of the site's branch locator page) come from the Sitecore
    context of that page; `locale` is the site's URL prefix. `hours_kwargs` are the language tables passed to
    `OpeningHours.add_ranges_from_string`.
    """

    item_attributes = {"brand": "Adecco", "brand_wikidata": "Q353494"}
    site_name: str
    language: str
    root_path_id: str
    locale: str
    hours_kwargs: dict[str, Any] = {}
    # Use the city as branch name, when branch names are business lines or just "Adecco".
    branch_from_city = False
    # "<postcode> <city>" is in AddressExtension, ZipCode and City are empty.
    postcode_in_address_extension = False
    # Branch names to skip (head offices, other group brands), per site.
    excluded: re.Pattern | None = None
    # A page of 300 takes the server ~11s; a site that needs more sets its own page size.
    page_size = 300
    max_passes = 3
    # The API's two origin servers have diverging search indexes: one sometimes returns degraded
    # pages, and they can disagree on recent changes. Asking again is the only way to switch.
    max_retries = 10
    custom_settings = {"DOWNLOAD_TIMEOUT": 30}

    def make_request(self, state: dict, page: int) -> Request:
        return Request(
            url="https://www.adecco.com/api/data/branches/getBranches",
            method="POST",
            # No Content-Type header: the API answers 500 to application/json.
            body=json.dumps(
                {
                    "rootPathId": self.root_path_id,
                    "templateId": "db798859-7992-4bfc-8db1-ee4a27ff9ee6",
                    "language": self.language,
                    "siteName": self.site_name,
                    "pageSize": self.page_size,
                    "skip": page,
                }
            ),
            cb_kwargs={"state": state},
            errback=self.parse_error,
            dont_filter=True,
        )

    async def start(self) -> AsyncIterator[Request]:
        state = {"entries": {}, "origins": {}, "total": 0, "requests": 0, "new_in_pass": 0, "retries": 0, "tried": []}
        yield self.make_request(state | {"distrusted": None}, 0)

    def parse(self, response: TextResponse, state: dict) -> Iterable[Feature | Request]:
        # Origin servers also return pages in a different order, so entries repeat or go missing
        # between pages: walk all pages again until a whole pass adds nothing new.
        try:
            results = response.json()["swpsearch"]
            listed = [
                (
                    (
                        {
                            field["name"]: field.get("value")
                            for field in result.get("fields") or []
                            if field.get("name")
                        },
                        (result.get("url") or {}).get("path"),
                    )
                    if result
                    else None
                )
                for result in results.get("results") or []
            ]
        except (AttributeError, KeyError, TypeError, ValueError):
            # Not the expected JSON: retried like a degraded page.
            results, listed = {}, [None]

        degraded = self.is_degraded(listed)
        origin = ":".join((response.headers.get("x-origin-server") or b"").decode().split(":")[:2])
        if degraded and origin and state["distrusted"] is None:
            # A server that returned a degraded page can also return shifted or outdated pages with
            # no visible sign: drop what only it returned and walk the pages again without it.
            state["distrusted"] = origin
            state["entries"] = {
                key: entry for key, entry in state["entries"].items() if state["origins"][key] - {origin}
            }
            state["total"] = state["requests"] = state["new_in_pass"] = 0
        elif degraded and origin and origin != state["distrusted"]:
            # Both servers returned degraded pages: no preference left.
            state["distrusted"] = ""
        untrusted = degraded or (origin and origin == state["distrusted"])
        state["tried"].append(origin or "?")
        if untrusted and state["retries"] < self.max_retries:
            state["retries"] += 1
            yield self.make_request(state, state["requests"] % max(ceil(state["total"] / self.page_size), 1))
            return
        if untrusted:
            self.logger.warning(
                f"Keeping a page with no acceptable answer in {len(state['tried'])} tries"
                f" (origin servers: {dict(Counter(state['tried']))}, last one degraded: {degraded})"
            )
        state["retries"] = 0
        state["tried"] = []
        # A degraded page's total is wrong either way: only use it when there is no other one yet.
        if not degraded or not state["total"]:
            state["total"] = max(state["total"], results.get("total") or 0)
        pages = max(ceil(state["total"] / self.page_size), 1)

        entries = state["entries"]
        seen = len(entries)
        # Identical entries can be listed several times within a page: number them so they still
        # count towards the total, while a repeat across pages collapses.
        occurrences = Counter()
        for branch, path in filter(None, listed):
            key = json.dumps([path, branch], sort_keys=True)
            numbered = f"{key}#{occurrences[key]}"
            entries[numbered] = (branch, path)
            state["origins"].setdefault(numbered, set()).add(origin)
            occurrences[key] += 1
        state["new_in_pass"] += len(entries) - seen
        state["requests"] += 1

        if state["requests"] % pages:
            yield self.make_request(state, state["requests"] % pages)
            return
        passes = state["requests"] // pages
        complete = len(entries) >= state["total"] and (pages == 1 or (passes > 1 and not state["new_in_pass"]))
        if not complete and passes < self.max_passes:
            state["new_in_pass"] = 0
            yield self.make_request(state, 0)
            return
        if len(entries) < state["total"]:
            self.logger.warning(f"Only {len(entries)} of {state['total']} branches found")
        yield from self.parse_branches(state)

    def is_degraded(self, listed: list) -> bool:
        # A degraded page has null results, or blank entries in place of some branches; a blank twin
        # next to a real entry at the same path is normal.
        if None in listed:
            return True
        filled = [any(branch.get(key) for key in ("BranchName", "Address", "Latitude")) for branch, _ in listed]
        filled_paths = {path for (_, path), has_data in zip(listed, filled) if has_data}
        return any(not has_data and path not in filled_paths for (_, path), has_data in zip(listed, filled))

    def parse_error(self, failure) -> Iterable[Feature]:
        # Keep what earlier pages returned rather than losing the whole site.
        self.logger.warning(f"Paging stopped early: {failure.value!r}")
        yield from self.parse_branches(failure.request.cb_kwargs["state"])

    def parse_branches(self, state: dict) -> Iterable[Feature]:
        # A branch can be listed several times with diverging data.
        candidates = defaultdict(list)
        for branch, path in state["entries"].values():
            if self.excluded and self.excluded.search((branch.get("BranchName") or "").strip()):
                continue
            if path and branch.get("Latitude"):
                candidates[self.get_ref(branch, path)].append((branch, path))

        items = []
        for ref, duplicates in candidates.items():
            # Prefer Partoo-synced entries over older hand-entered ones (FR, French day names), then the
            # entry whose own URL or BranchCode matches the ref, then a stable order.
            branch, path = min(
                duplicates,
                key=lambda entry: (
                    (entry[0].get("Schedules") or "").startswith("Lundi="),
                    not entry[1].lower().endswith("/" + ref.lower()),
                    entry[0].get("BranchCode") != ref,
                    entry[1],
                ),
            )

            item = Feature()
            item["ref"] = ref
            item["postcode"] = branch.get("ZipCode")
            item["city"] = branch.get("City")
            address_lines = [branch.get("Address"), branch.get("AddressExtension")]
            if self.postcode_in_address_extension and (
                m := re.fullmatch(r"(\d{4,5}) (.+)", (address_lines[1] or "").strip())
            ):
                item["postcode"], item["city"] = m.groups()
                address_lines.pop()
            item["street_address"] = merge_address_lines(address_lines)
            if self.branch_from_city:
                item["branch"] = item["city"]
            else:
                item["branch"] = (branch.get("BranchName") or "").strip().removeprefix("Adecco").strip() or None
            item["state"] = branch.get("State")
            item["lat"] = branch.get("Latitude")
            item["lon"] = branch.get("Longitude")
            item["phone"] = branch.get("PhoneNumber")
            item["email"] = branch.get("Mail")
            # Some sites (IT) already include the locale in the path.
            prefix = "" if path.startswith(f"/{self.locale}/") else f"/{self.locale}"
            item["website"] = f"https://www.adecco.com{prefix}{path}"

            hours = "; ".join(f"{days} {times}" for days, times in parse_qsl(branch.get("Schedules") or ""))
            oh = OpeningHours()
            try:
                oh.add_ranges_from_string(self.pre_process_schedules(hours), **self.hours_kwargs)
            except (IndexError, KeyError, ValueError):
                pass
            # Some branches are listed as closed every day; publish no hours for them.
            if oh.day_hours:
                item["opening_hours"] = oh

            apply_category(Categories.OFFICE_EMPLOYMENT_AGENCY, item)
            items.append((item, branch))

        # Some sites show a national helpline instead of the branch's own phone or mail (every PL
        # branch, most ES ones).
        for key, normalise in (("phone", lambda value: re.sub(r"\D", "", value)), ("email", str.lower)):
            counts = Counter(normalise(item[key]) for item, _ in items if item.get(key))
            for item, _ in items:
                if item.get(key) and counts[normalise(item[key])] > max(3, len(items) / 4):
                    item[key] = None

        for item, branch in items:
            yield from self.post_process_item(item, branch)

    def get_ref(self, branch: dict, path: str) -> str:
        # BranchCode is reused across distinct branches; PartooCode (when set) matches each
        # branch's own mail address, except placeholder "PTOCODE<n>" values, which are shared.
        partoo = branch.get("PartooCode") or ""
        if partoo and not partoo.startswith("PTOCODE"):
            return partoo
        # The last segment alone repeats across cities ("/oficinas/<province>/<city>/adecco-staffing").
        return "/".join(path.rstrip("/").rsplit("/", 2)[-2:])

    def pre_process_schedules(self, hours: str) -> str:
        return hours

    def post_process_item(self, item: Feature, branch: dict) -> Iterable[Feature]:
        yield item
