import json
import re
from collections import defaultdict
from html import unescape
from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature

POSTCODE_RE = re.compile(r"\b(\d{5})\b")
UNIT_SUFFIX_RE = re.compile(r"\s+(Counter|Delivery|Stores)$")


class MauritiusPostMUSpider(Spider):
    name = "mauritius_post_mu"
    item_attributes = {"operator": "Mauritius Post", "operator_wikidata": "Q2389598"}
    allowed_domains = ["www.mauritiuspost.mu"]
    start_urls = ["https://www.mauritiuspost.mu/locate-a-post-office/"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        offices = json.loads(response.xpath('//script[@id="post-offices-lists-json"]/text()').get())["data"]

        # Some titles carry the postcode and street after the place name ("Moka 80827 Minissy Rd Moka").
        for office in offices:
            office["title"] = unescape(office["title"]).replace("’", "'").strip()
            office["branch"] = POSTCODE_RE.split(office["title"])[0].strip()

        # Counter, delivery and stores units of one office legitimately share a position, but a few
        # unrelated offices (e.g. Port Mathurin and Mont Lubin) share one too: drop those positions.
        sites = defaultdict(set)
        for office in offices:
            sites[(office["latitude"], office["longitude"])].add(UNIT_SUFFIX_RE.sub("", office["branch"]))

        seen = set()
        for office in offices:
            if office["branch"] == "Postal Museum":
                continue
            address = unescape(office["address"]).replace("’", "'").strip()
            postcode = POSTCODE_RE.search(address)
            ref = office["title"]
            if ref in seen:  # "Poste De Flacq" is listed twice
                ref = "{} {}".format(ref, postcode.group(1) if postcode else address)
            seen.add(ref)

            item = Feature()
            item["ref"] = ref
            item["branch"] = office["branch"]
            item["addr_full"] = address
            if postcode:
                item["postcode"] = postcode.group(1)
            item["phone"] = re.sub(r"(?i)^tel\s*:\s*|\s*-\s*delivery$", "", office["phone"]).replace("/", ";") or None
            item["email"] = re.sub(r"(?i)^email", "", office["email"]) or None
            if len(sites[(office["latitude"], office["longitude"])]) == 1:
                item["lat"], item["lon"] = office["latitude"], office["longitude"]
            region = office["category"][0]["name"] if office["category"] else None
            if region in ("Rodgriues", "Agalega"):
                item["state"] = "Rodrigues" if region == "Rodgriues" else region
            item["country"] = "MU"

            if office["branch"].endswith(("Delivery", "Stores")):
                apply_category(Categories.POST_DEPOT, item)  # delivery/stores units have no public counter
            else:
                apply_category(Categories.POST_OFFICE, item)
            yield item
