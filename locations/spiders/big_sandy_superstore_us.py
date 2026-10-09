import json
import re
from typing import Iterable

import scrapy
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.items import Feature
from locations.user_agents import BROWSER_DEFAULT

SITEMAP_URL = "https://cdn.avbportal.com/magento-media/sitemaps/bigs1/sitemap.xml"
WANTED_TYPES = {"FurnitureStore", "HomeGoodsStore", "LocalBusiness"}


class BigSandySuperstoreUSSpider(scrapy.Spider):
    name = "big_sandy_superstore_us"
    item_attributes = {
        "brand_wikidata": "Q4906290",
        "name": "Big Sandy Superstore",
    }
    custom_settings = {"USER_AGENT": BROWSER_DEFAULT}
    start_urls = ["https://www.bigsandysuperstore.com/"]

    def parse(self, response: Response) -> Iterable[scrapy.Request]:
        # A JSON blob embedded on every page lists all "main" stores with an
        # accurate phone/lat/lon per store. Individual store landing pages
        # sometimes carry stale copy-pasted phone/postcode/geo data (e.g. the
        # Portsmouth and Dublin pages), so this blob is used as the
        # authoritative source, keyed by house number (unique across all
        # stores, unlike phone or postcode which are sometimes duplicated by
        # the stale-page bug).
        next_data = json.loads(response.xpath('//script[@id="__NEXT_DATA__"]/text()').get())
        stores = next_data["props"]["pageProps"]["initialState"]["appSlice"]["config"]["store_locations"]
        self.store_by_housenumber = {}
        for store in stores:
            if m := re.match(r"(\d+)", store["address"]):
                self.store_by_housenumber[m.group(1)] = store

        yield scrapy.Request(SITEMAP_URL, callback=self.parse_sitemap)

    def parse_sitemap(self, response: Response) -> Iterable[scrapy.Request]:
        response.selector.remove_namespaces()
        for url in response.xpath("//loc/text()").getall():
            if "/locations/" not in url:
                continue
            if url.endswith("-clearance"):
                # Clearance center pages share the exact same address (and
                # therefore the same physical building) as their parent
                # superstore page, so they are not separate locations.
                continue
            yield scrapy.Request(url, callback=self.parse_store)

    def parse_store(self, response: Response) -> Iterable[Feature]:
        store_ld = self.extract_store_ld(response)

        if store_ld:
            item = DictParser.parse(store_ld)
            # The per-location name is inconsistent across page templates
            # (sometimes just the brand, sometimes "Brand - City"); a
            # cleaner, consistent branch name is derived below instead.
            item.pop("name", None)
        else:
            item = Feature()

        self.apply_store_list_data(item, response)

        if not item.get("phone"):
            # Some pages (e.g. Florence) carry a "tel:" link but no phone
            # number in their structured data.
            if m := re.search(r'href="tel:([+0-9-]+)"', response.text):
                item["phone"] = m.group(1)

        item["website"] = response.url
        item["country"] = "US"

        if store_ld and (oh := self.parse_opening_hours(store_ld)):
            item["opening_hours"] = oh

        apply_category(Categories.SHOP_FURNITURE, item)

        yield item

    def apply_store_list_data(self, item: Feature, response: Response) -> None:
        # A JSON blob embedded on every page lists all "main" stores with an
        # accurate phone/lat/lon per store. Individual store landing pages
        # sometimes carry stale copy-pasted phone/postcode/geo data (e.g. the
        # Portsmouth page shows Lancaster's postcode and a third store's
        # phone number), so this list is used as the authoritative source,
        # matched by house number (unique across all stores, unlike phone or
        # postcode which are sometimes duplicated by the stale-page bug).
        housenumber = None
        if item.get("street_address") and (m := re.match(r"(\d+)", item["street_address"])):
            housenumber = m.group(1)

        matched_store = self.store_by_housenumber.get(housenumber) if housenumber else None
        if not matched_store:
            # Fall back to matching the URL slug against a store's name, for
            # a store page with no usable structured data at all (e.g.
            # Chesapeake) or one not present in the store list (e.g. Florence).
            slug_words = set(response.url.rsplit("/", 1)[-1].split("-"))
            for store in self.store_by_housenumber.values():
                if set(store["store_name"].lower().split()) & slug_words:
                    matched_store = store
                    break

        if not matched_store:
            slug = response.url.rsplit("/", 1)[-1]
            item["ref"] = slug
            item["branch"] = slug.replace("big-sandy-", "").replace("-", " ").title()
            return

        item["ref"] = matched_store["google_code"]
        item["phone"] = matched_store["phone"]
        item["lat"] = matched_store["latitude"]
        item["lon"] = matched_store["longitude"]
        item["branch"] = re.sub(r"\s*(Superstore|Furniture & Mattress)\s*$", "", matched_store["store_name"])
        if m := re.search(r"(\d{5})\s*$", matched_store["address"]):
            item["postcode"] = m.group(1)
        if not item.get("street_address") and not item.get("addr_full"):
            # This page had no usable structured data at all (e.g.
            # Chesapeake); the store list's address string isn't reliably
            # splittable into street/city, so use it whole.
            item["addr_full"] = matched_store["address"]

    @staticmethod
    def parse_opening_hours(store_ld: dict) -> OpeningHours:
        oh = OpeningHours()

        if isinstance(store_ld.get("openingHours"), str):
            # e.g. "Mo,Tu,We,Th,Fr,Sa 10:00-21:00"
            days_part, _, times_part = store_ld["openingHours"].partition(" ")
            if "-" in times_part:
                opens, closes = times_part.split("-", 1)
                oh.add_days_range(days_part.split(","), opens, closes)

        specs = store_ld.get("openingHoursSpecification")
        for spec in ([specs] if isinstance(specs, dict) else specs or []):
            days = spec.get("dayOfWeek")
            if not days:
                continue
            days = days if isinstance(days, list) else [days]
            if spec.get("opens") and spec.get("closes"):
                oh.add_days_range(days, spec["opens"], spec["closes"])

        return oh

    @staticmethod
    def extract_store_ld(response: Response) -> dict | None:
        for block in response.xpath('//script[@type="application/ld+json"]/text()').getall():
            try:
                obj = json.loads(block, strict=False)
            except json.JSONDecodeError:
                try:
                    obj, _ = json.JSONDecoder().raw_decode(block.strip())
                except json.JSONDecodeError:
                    continue

            nodes = obj.get("@graph", [obj]) if isinstance(obj, dict) else obj
            for node in nodes or []:
                if node and node.get("@type") in WANTED_TYPES:
                    return node

        return None
