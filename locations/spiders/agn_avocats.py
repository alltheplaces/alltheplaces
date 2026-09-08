import re
from typing import Iterable

from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider

DAYS_FR = {
    "lundi": "Mo",
    "mardi": "Tu",
    "mercredi": "We",
    "jeudi": "Th",
    "vendredi": "Fr",
    "samedi": "Sa",
    "dimanche": "Su",
}
DAY_ORDER = list(DAYS_FR.keys())

TIME_RANGE_RE = re.compile(r"(\d{1,2}[:h]\d{2})\s*-\s*(\d{1,2}[:h]\d{2})")
DAY_LINE_RE = re.compile(
    r"^(lundi|mardi|mercredi|jeudi|vendredi|samedi|dimanche)"
    r"(?:\s*(?:au|-)\s*(lundi|mardi|mercredi|jeudi|vendredi|samedi|dimanche))?"
    r"\s+(.*)$",
    re.IGNORECASE,
)


class AgnAvocatsSpider(SitemapSpider, StructuredDataSpider):
    name = "agn_avocats"
    item_attributes = {"brand": "AGN Avocats", "brand_wikidata": "Q141355112"}
    sitemap_urls = ["https://www.agn-avocats.fr/page-sitemap.xml"]
    sitemap_rules = [(r"^https://www\.agn-avocats\.fr/[^/]+/?$", "parse_sd")]
    wanted_types = ["LegalService"]
    drop_attributes = {"image", "twitter", "facebook"}

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        if item.get("phone") == "09 72 34 24 72":
            item["phone"] = None

        item["opening_hours"] = self.parse_hours(response)

        apply_category(Categories.OFFICE_LAWYER, item)
        yield item

    def parse_hours(self, response: TextResponse) -> OpeningHours:
        oh = OpeningHours()

        texts = [t.strip().replace("\xa0", " ") for t in response.xpath("//text()").getall()]
        texts = [t for t in texts if t]

        for text in texts:
            match = DAY_LINE_RE.match(text)
            if not match:
                continue

            start_day, end_day, rest = match.groups()
            start_day = start_day.lower()

            if end_day:
                end_day = end_day.lower()
                start_idx = DAY_ORDER.index(start_day)
                end_idx = DAY_ORDER.index(end_day)
                days = DAY_ORDER[start_idx : end_idx + 1]
            else:
                days = [start_day]

            if "rendez-vous" in rest.lower() or "fermé" in rest.lower():
                continue

            for open_time, close_time in TIME_RANGE_RE.findall(rest):
                open_time = open_time.replace("h", ":")
                close_time = close_time.replace("h", ":")
                for day in days:
                    if osm_day := DAYS_FR.get(day):
                        oh.add_range(osm_day, open_time, close_time, time_format="%H:%M")

        return oh
