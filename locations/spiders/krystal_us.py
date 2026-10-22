import re
from typing import Any

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.structured_data_spider import StructuredDataSpider


class KrystalUSSpider(SitemapSpider, StructuredDataSpider):
    name = "krystal_us"
    item_attributes = {"brand": "Krystal", "brand_wikidata": "Q472195"}
    allowed_domains = ["www.krystal.com"]
    sitemap_urls = ["http://www.krystal.com/sitemap.xml"]
    sitemap_rules = [(r"\/locations\/[a-z]{2}\/[\w\-]+\/[\w\-]+\/?$", "parse_sd")]

    def post_process_item(self, item: Any, response: Response, ld_data: dict, **kwargs: Any) -> Any:
        item["ref"] = item["website"] = response.url
        item.pop("name", None)
        apply_category(Categories.FAST_FOOD, item)

        item["opening_hours"] = OpeningHours()
        for hours_column in response.xpath('//div[@class="hours"]/div[@class="col"]'):
            day_names = hours_column.xpath('./div[@class="day"]/p/span/text()').getall()
            times = hours_column.xpath('./div[@class="time"]/p/span/text()').getall()
            for day, hours in zip(day_names, times):
                hours = hours.upper().replace("OPEN 24 HOURS", "12AM-12AM")
                if "CLOSED" in hours:
                    item["opening_hours"].set_closed(day)
                    continue
                open_time, close_time = hours.split("-", 1)
                if ":" not in open_time:
                    open_time = open_time.replace("AM", ":00AM").replace("PM", ":00PM")
                if ":" not in close_time:
                    close_time = close_time.replace("AM", ":00AM").replace("PM", ":00PM")
                item["opening_hours"].add_range(day, open_time, close_time, "%I:%M%p")

        if m := re.search(r"\w\w\.lat=(-?\d+\.\d+);\w\w\.lng=(-?\d+\.\d+)", response.text):
            item["lat"], item["lon"] = m.groups()
        yield item
