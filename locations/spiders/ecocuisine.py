import re
from typing import Iterable

from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.hours import DAYS_FR, OpeningHours, sanitise_day
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider

TIME_RANGE_RE = re.compile(r"(\d{1,2}[:h]\d{2})\s*-\s*(\d{1,2}[:h]\d{2})")


class EcocuisineSpider(SitemapSpider, StructuredDataSpider):
    name = "ecocuisine"
    item_attributes = {"brand": "Ecocuisine", "brand_wikidata": "Q141349333"}
    sitemap_urls = ["https://www.ecocuisine.fr/sitemap.xml"]
    sitemap_rules = [(r"https://www.ecocuisine.fr/magasins/\d.*", "parse_sd")]
    wanted_types = ["HomeAndConstructionBusiness"]
    drop_attributes = {"image"}

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        if item.get("facebook") == "https://www.facebook.com/ecocuisine.officiel":
            item["facebook"] = None
        item["branch"] = item.pop("name").removeprefix("ECOCUISINE ")

        item["opening_hours"] = self.parse_hours(response)

        apply_category(Categories.SHOP_KITCHEN, item)
        yield item

    def parse_hours(self, response: TextResponse) -> OpeningHours:
        oh = OpeningHours()
        closed_days = []

        rows = response.xpath('//*[contains(text(),"Horaires d\'ouverture")]/following-sibling::ul[1]/li')

        for row in rows:
            text = " ".join(row.xpath(".//text()").getall())
            text = text.replace("\xa0", " ").strip()
            if ":" not in text and "h" not in text.lower():
                continue

            day_part, _, hours_part = text.partition(":")
            day_part = day_part.strip()
            hours_part = hours_part.strip()

            if "fermé" in hours_part.lower():
                osm_day = sanitise_day(day_part, DAYS_FR)
                if osm_day:
                    closed_days.append(osm_day)
                continue

            if "-" in day_part:
                start_day_raw, end_day_raw = [d.strip() for d in day_part.split("-")]
                start_day = sanitise_day(start_day_raw, DAYS_FR)
                end_day = sanitise_day(end_day_raw, DAYS_FR)
                if start_day and end_day:
                    days_order = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]
                    start_idx = days_order.index(start_day)
                    end_idx = days_order.index(end_day)
                    days = days_order[start_idx : end_idx + 1]
                else:
                    continue
            else:
                osm_day = sanitise_day(day_part, DAYS_FR)
                days = [osm_day] if osm_day else []

            for open_time, close_time in TIME_RANGE_RE.findall(hours_part):
                open_time = open_time.replace("h", ":")
                close_time = close_time.replace("h", ":")
                for day in days:
                    oh.add_range(day, open_time, close_time, time_format="%H:%M")

        if closed_days:
            oh.set_closed(closed_days)

        return oh
