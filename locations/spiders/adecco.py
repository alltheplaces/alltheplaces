import json
from collections import defaultdict
from math import ceil
from typing import AsyncIterator, Iterable
from urllib.parse import parse_qsl

from scrapy import Request, Spider
from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.hours import (
    CLOSED_DE,
    CLOSED_EN,
    CLOSED_FR,
    DAYS_DE,
    DAYS_EN,
    DAYS_FR,
    DELIMITERS_DE,
    DELIMITERS_EN,
    OpeningHours,
)
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines


class AdeccoSpider(Spider):
    name = "adecco"
    item_attributes = {"brand": "Adecco", "brand_wikidata": "Q353494"}
    # One Sitecore site per country. root_path_id is the item ID of the site's branch locator page,
    # language/site_name come from that page's Sitecore context.
    sites = [
        {
            "country": "FR",
            "locale": "fr-fr",
            "site_name": "AdeccoFR",
            "language": "fr-FR",
            "root_path_id": "cfb5e9b3-b605-4c23-92c8-25eb759f3de5",
            "days": DAYS_FR,
            "closed": CLOSED_FR,
        },
        {
            "country": "DE",
            "locale": "de-de",
            "site_name": "AdeccoDE",
            "language": "de-DE",
            "root_path_id": "fc78aa73-6665-404d-b5fb-8ebe2e9993ff",
            "days": DAYS_DE,
            "closed": CLOSED_DE,
            "delimiters": DELIMITERS_DE,
        },
    ]
    page_size = 250
    max_passes = 3
    max_retries = 3
    # A page of 250 takes the server ~9s.
    custom_settings = {"DOWNLOAD_TIMEOUT": 30}

    def make_request(self, state: dict, page: int) -> Request:
        site = state["site"]
        return Request(
            url="https://www.adecco.com/api/data/branches/getBranches",
            method="POST",
            # No Content-Type header: the API answers 500 to application/json.
            body=json.dumps(
                {
                    "rootPathId": site["root_path_id"],
                    "templateId": "db798859-7992-4bfc-8db1-ee4a27ff9ee6",
                    "language": site["language"],
                    "siteName": site["site_name"],
                    "pageSize": self.page_size,
                    "skip": page,
                }
            ),
            cb_kwargs={"state": state},
            errback=self.parse_error,
            dont_filter=True,
        )

    async def start(self) -> AsyncIterator[Request]:
        for site in self.sites:
            yield self.make_request(
                {"site": site, "entries": {}, "total": 0, "requests": 0, "new_in_pass": 0, "retries": 0}, 0
            )

    def parse(self, response: TextResponse, state: dict) -> Iterable[Feature | Request]:
        # Pages can come from search replicas that differ in order and content, so entries repeat
        # or go missing between pages: walk all pages again until a whole pass adds nothing new.
        results = response.json().get("swpsearch") or {}
        state["total"] = max(state["total"], results.get("total") or 0)
        pages = max(ceil(state["total"] / self.page_size), 1)
        # Only the page of a degraded replica that holds its null result shows it; that page lacks
        # some branches and is re-requested.
        if None in (results.get("results") or []):
            if state["retries"] < self.max_retries:
                state["retries"] += 1
                yield self.make_request(state, state["requests"] % pages)
                return
            self.logger.warning(f"Keeping a degraded page for {state['site']['locale']}")
        state["retries"] = 0
        entries = state["entries"]
        seen = len(entries)
        for result in results.get("results") or []:
            if not result:
                continue
            branch = {field["name"]: field.get("value") for field in result.get("fields") or [] if field}
            path = (result.get("url") or {}).get("path")
            entries[json.dumps([path, branch], sort_keys=True)] = (branch, path)
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
            self.logger.warning(f"Only {len(entries)} of {state['total']} branches found for {state['site']['locale']}")
        yield from self.parse_branches(state)

    def parse_error(self, failure) -> Iterable[Feature]:
        # Keep what earlier pages returned rather than losing the whole site.
        state = failure.request.cb_kwargs["state"]
        self.logger.warning(f"Paging stopped early for {state['site']['locale']}: {failure.value!r}")
        yield from self.parse_branches(state)

    def parse_branches(self, state: dict) -> Iterable[Feature]:
        site = state["site"]
        # BranchCode is reused across distinct branches; PartooCode (when set) matches each
        # branch's own mail address. A branch can be listed several times with diverging data.
        candidates = defaultdict(list)
        for branch, path in state["entries"].values():
            if path and branch.get("Latitude"):
                ref = branch.get("PartooCode") or "{}-{}".format(site["country"], path.rsplit("/", 1)[-1])
                candidates[ref].append((branch, path))

        for ref, duplicates in candidates.items():
            # Prefer Partoo-synced entries over older hand-entered ones (French day names).
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
            item["branch"] = (branch.get("BranchName") or "").strip().removeprefix("Adecco").strip() or None
            item["street_address"] = merge_address_lines([branch.get("Address"), branch.get("AddressExtension")])
            item["postcode"] = branch.get("ZipCode")
            item["city"] = branch.get("City")
            item["state"] = branch.get("State")
            # The CountryCode field is unreliable ("", "CAN", "Ireland" on other sites).
            item["country"] = site["country"]
            item["lat"] = branch.get("Latitude")
            item["lon"] = branch.get("Longitude")
            item["phone"] = branch.get("PhoneNumber")
            item["email"] = branch.get("Mail")
            item["website"] = "https://www.adecco.com/{}{}".format(site["locale"], path)

            hours = "; ".join(f"{days} {times}" for days, times in parse_qsl(branch.get("Schedules") or ""))
            item["opening_hours"] = OpeningHours()
            item["opening_hours"].add_ranges_from_string(
                hours.replace(" und ", ", "),
                days=DAYS_EN | site["days"],
                closed=CLOSED_EN + site.get("closed", []),
                delimiters=site.get("delimiters", DELIMITERS_EN),
            )

            apply_category(Categories.OFFICE_EMPLOYMENT_AGENCY, item)
            yield item
