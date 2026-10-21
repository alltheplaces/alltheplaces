import re
from typing import Any, Iterable

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider

DAY_GROUPS = {"L-V": ["Mo", "Tu", "We", "Th", "Fr"], "S": ["Sa"], "D": ["Su"]}


class FotoprixESSpider(SitemapSpider, StructuredDataSpider):
    name = "fotoprix_es"
    item_attributes = {
        "brand": "Fotoprix",
        "brand_wikidata": "Q99196842",
    }
    sitemap_urls = ["https://www.fotoprix.com/robots.txt"]
    sitemap_rules = [
        (r"https://www.fotoprix.com/tiendas/[\w-]+/[\w-]+", "parse"),
    ]
    drop_attributes = {"image"}

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs: Any) -> Iterable[Feature]:
        item["branch"] = item.pop("name").removeprefix("Fotoprix ")
        if match := re.match(r"(?:\d+\s+)?Phone House\s+(?:\d+\s+)?(.+)", item["branch"], re.IGNORECASE):
            item["branch"] = match.group(1)
            item["located_in"] = "Phone House"
        apply_category(Categories.SHOP_PHOTO, item)
        item["opening_hours"] = oh = OpeningHours()
        for line in response.xpath('//p[text()="Horario:"]/following-sibling::p/text()').getall():
            day_group, _, hours = line.partition(":")
            if not (days := DAY_GROUPS.get(day_group.strip())):
                continue
            hours = re.sub(r"\(.*?\)", "", hours)
            if re.search(r"cerrado|no abrimos", hours, re.IGNORECASE):
                oh.set_closed(days)
                continue
            hours = re.sub(r"(\d)\.(\d)", r"\1:\2", hours)
            for start_time, end_time in re.findall(
                r"(?<![\d:])(\d{1,2}(?::\d{2})?)\s*(?:a|-|–)\s*(\d{1,2}(?::\d{2})?)(?![\d:])", hours
            ):
                oh.add_days_range(days, *(t if ":" in t else f"{t}:00" for t in (start_time, end_time)))
        yield item
