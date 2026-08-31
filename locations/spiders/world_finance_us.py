from typing import Iterable

from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider

from locations.hours import OpeningHours
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class WorldFinanceUSSpider(SitemapSpider, StructuredDataSpider):
    name = "world_finance_us"
    item_attributes = {"brand": "World Finance", "brand_wikidata": "Q3569971"}
    sitemap_urls = ["https://www.loansbyworld.com/sitemap.xml"]
    sitemap_rules = [("/branches/", "parse_sd")]

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        item.pop("name")
        try:
            oh = OpeningHours()
            for day_time in ld_data.get("openingHoursSpecification"):
                day = day_time.get("dayOfWeek")
                time = day_time.get("opens")
                if time == "Closed":
                    oh.set_closed(day)
                elif time:
                    open_time, close_time = time.split("-")
                    oh.add_range(day=day, open_time=open_time, close_time=close_time, time_format="%I:%M%p")
            item["opening_hours"] = oh
        except:
            pass
        yield item
