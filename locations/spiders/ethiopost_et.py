import json
import re
from collections import defaultdict
from html import unescape
from typing import Any

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.items import Feature

BRANCH_SUFFIX_RE = re.compile(r"\s*(?:Branch\s+)?Post\s+Office(?:\s+Branch)?\s*$", re.IGNORECASE)


class EthiopostEtSpider(Spider):
    name = "ethiopost_et"
    item_attributes = {"operator": "Ethiopian Postal Service", "operator_wikidata": "Q16878216"}
    allowed_domains = ["ethio.post"]
    # The map page carries every branch's coordinates (JetEngine map listing "data-markers"); the
    # names and taxonomy terms come from the WordPress REST API of the "branches" post type.
    start_urls = ["https://ethio.post/branches/"]
    api = "https://ethio.post/wp-json/wp/v2/"

    def parse(self, response: Response, **kwargs: Any) -> Any:
        markers = {}
        for blob in response.xpath("//@data-markers").getall():
            for marker in json.loads(blob):
                markers[marker["id"]] = marker["latLang"]
        yield JsonRequest(
            self.api + "branch-region?per_page=100&_fields=id,name",
            callback=self.parse_regions,
            cb_kwargs={"markers": markers},
        )

    def parse_regions(self, response: Response, markers: dict) -> Any:
        regions = {term["id"]: unescape(term["name"]) for term in response.json()}
        yield JsonRequest(
            self.api + "branch-services?per_page=100&_fields=id,name",
            callback=self.parse_services,
            cb_kwargs={"markers": markers, "regions": regions},
        )

    def parse_services(self, response: Response, markers: dict, regions: dict) -> Any:
        services = {term["id"]: unescape(term["name"]) for term in response.json()}
        yield self.branches_request(1, markers, regions, services, [])

    def branches_request(self, page: int, markers: dict, regions: dict, services: dict, branches: list) -> JsonRequest:
        return JsonRequest(
            self.api + "branches?per_page=100&page={}&_fields=id,title,link,branch-region,branch-services".format(page),
            callback=self.parse_branches,
            cb_kwargs={
                "page": page,
                "markers": markers,
                "regions": regions,
                "services": services,
                "branches": branches,
            },
        )

    def parse_branches(
        self, response: Response, page: int, markers: dict, regions: dict, services: dict, branches: list
    ) -> Any:
        branches.extend(response.json())
        if page < int(response.headers.get("X-WP-TotalPages", 1)):
            yield self.branches_request(page + 1, markers, regions, services, branches)
            return

        items = [self.make_item(branch, markers.get(branch["id"]), regions, services) for branch in branches]

        # Some positions hold two posts: either the same office entered twice (keep one copy), or
        # unrelated offices on a placeholder spot such as Ethiopia's centroid (drop the position).
        stacks = defaultdict(list)
        for item in items:
            if item.get("lat") is not None:
                stacks[(item["lat"], item["lon"])].append(item)
        duplicates = set()
        for stack in stacks.values():
            if len(stack) < 2:
                continue
            if len({item["branch"].lower() for item in stack}) == 1:
                duplicates.update(item["ref"] for item in sorted(stack, key=lambda i: int(i["ref"]))[1:])
            else:
                for item in stack:
                    item.pop("lat"), item.pop("lon")

        for item in items:
            if item["ref"] not in duplicates:
                yield item

    def make_item(self, branch: dict, position: dict | None, regions: dict, services: dict) -> Feature:
        title = unescape(branch["title"]["rendered"]).strip()
        amharic, _, english = title.rpartition(" / ")
        item = Feature()
        item["ref"] = str(branch["id"])
        item["website"] = branch["link"]
        item["branch"] = BRANCH_SUFFIX_RE.sub("", english or title).strip()
        if amharic:
            item["extras"]["branch:am"] = re.sub(r"\s*ቅርንጫፍ\s*ፖ/ቤት\s*$", "", amharic).strip()
        if region_ids := branch.get("branch-region"):
            item["state"] = regions.get(region_ids[0])
        if position:
            try:
                lat, lon = float(position["lat"]), float(position["lng"])
            except (TypeError, ValueError):
                lat = lon = None
            if lat is not None and 3.4 < lat < 14.9 and 32.9 < lon < 48.0:
                item["lat"], item["lon"] = lat, lon
        item["country"] = "ET"
        apply_category(Categories.POST_OFFICE, item)
        return item
