import re
from typing import Iterable

from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.hours import sanitise_day
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class TokmanniFISpider(SitemapSpider, StructuredDataSpider):
    name = "tokmanni_fi"
    item_attributes = {"brand": "Tokmanni", "brand_wikidata": "Q13423470"}
    sitemap_urls = ["https://www.tokmanni.fi/sitemap/sitemap.xml"]
    sitemap_rules = [(r"/store/[^/]+/?$", "parse_sd")]

    def pre_process_data(self, ld_data: dict, **kwargs):
        # "Suljettu" marks an explicitly closed day and bare hours ("8-20:00") break strptime.
        hours = ld_data.get("openingHours")
        if isinstance(hours, str):
            hours = [hours]
        fixed = []
        for rule in hours or []:
            if not isinstance(rule, str):
                continue
            days, sep, times = rule.strip().partition(" ")
            if not sep:
                retry = re.split(r"\s+", rule.strip(), maxsplit=1)
                if len(retry) > 1:
                    days, times = retry
            days = re.sub(r"\s+", "", days)
            if not times or not all(sanitise_day(p) for p in re.split(r"[,-]", days) if p):
                continue
            if "suljettu" in times.lower():
                fixed.append(f"{days} closed")
                continue
            times = times.replace("\u2013", "-").replace("\u2014", "-")
            if times.lower() in ("closed", "off"):
                fixed.append(f"{days} closed")
                continue
            ranges = []
            for part in times.split(","):
                start, sep, end = part.partition("-")
                start, end = start.strip(), end.strip()
                if not sep or not start or not end or "-" in end:
                    break
                ranges.append(f"{start if ':' in start else start + ':00'}-{end if ':' in end else end + ':00'}")
            else:
                fixed.append(f"{days} {','.join(ranges)}")
        ld_data["openingHours"] = fixed

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        if str(item.get("image") or "").endswith("/images/logo.svg"):
            item["image"] = None  # shared brand logo, not a store photo
        if item.get("facebook") == "https://www.facebook.com/Tokmanni.fi/":
            item["facebook"] = None
        if item.get("twitter") == "tokmanni":
            item["twitter"] = None
        # Only unambiguous floor markers split out; anything else stays in the street line.
        if floor := re.search(r"(?:\(\s*(\d+)\.\s*krs\)|,\s*(\d+)\s*krs)$", item.get("street_address") or ""):
            item["extras"]["addr:floor"] = floor.group(1) or floor.group(2)
            item["street_address"] = re.sub(
                r"\s*(?:\(\s*\d+\.\s*krs\)|,\s*\d+\s*krs)$", "", item["street_address"]
            ).strip()
        branch = (item.pop("name") or "").removeprefix("Tokmanni ").removeprefix("Tokmanni-")
        item["branch"] = branch if branch not in ("", "Tokmanni") else None
        apply_category(Categories.SHOP_VARIETY_STORE, item)
        yield item
