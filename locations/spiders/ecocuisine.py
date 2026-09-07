import re
from typing import Iterable

from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider

TIME_RANGE_RE = re.compile(r"(\d{1,2}[:h]\d{2})\s*-\s*(\d{1,2}[:h]\d{2})")


class AmbianceEtStylesFRSpider(SitemapSpider, StructuredDataSpider):
    name = "ecocuisine"
    item_attributes = {"brand": "Ecocuisine", "brand_wikidata": "Q141349333"}
    sitemap_urls = ["https://www.ecocuisine.fr/sitemap.xml"]
    sitemap_rules = [(r"https://www.ecocuisine.fr/magasins/\d.*", "parse_sd")]
    wanted_types = ["HomeAndConstructionBusiness"]
    drop_attributes = {"image"}

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

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        if item.get("facebook") == "https://www.facebook.com/ecocuisine.officiel":
            item["facebook"] = None
        item["branch"] = item.pop("name").removeprefix("ECOCUISINE ")

        item["opening_hours"] = self.parse_hours(response)

        apply_category(Categories.SHOP_KITCHEN, item)
        yield item

    def parse_hours(self, response: TextResponse) -> OpeningHours:
        oh = OpeningHours()

        rows = response.xpath(
            '//*[contains(text(),"Horaires d\'ouverture")]/following-sibling::ul[1]/li'
        )

        for row in rows:
            text = " ".join(row.xpath(".//text()").getall())
            text = text.replace("\xa0", " ").strip()
            if ":" not in text and "h" not in text.lower():
                continue

            day_part, _, hours_part = text.partition(":")
            day_part = day_part.strip().lower()
            hours_part = hours_part.strip()

            if "fermé" in hours_part.lower():
                continue

            if "-" in day_part:
                start_day, end_day = [d.strip() for d in day_part.split("-")]
                try:
                    start_idx = self.DAY_ORDER.index(start_day)
                    end_idx = self.DAY_ORDER.index(end_day)
                except ValueError:
                    continue
                days = self.DAY_ORDER[start_idx : end_idx + 1]
            else:
                days = [day_part]

            for open_time, close_time in TIME_RANGE_RE.findall(hours_part):
                open_time = open_time.replace("h", ":")
                close_time = close_time.replace("h", ":")
                for day in days:
                    if osm_day := self.DAYS_FR.get(day):
                        oh.add_range(osm_day, open_time, close_time, time_format="%H:%M")

        return oh
