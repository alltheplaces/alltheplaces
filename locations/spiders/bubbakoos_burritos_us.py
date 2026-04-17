import json
import re

from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider

from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.structured_data_spider import StructuredDataSpider


class BubbakoosBurritosUSSpider(SitemapSpider, StructuredDataSpider):
    name = "bubbakoos_burritos_us"
    item_attributes = {"brand": "Bubbakoo's Burritos", "brand_wikidata": "Q114619751"}
    sitemap_urls = ["https://locations.bubbakoos.com/sitemap.xml"]
    sitemap_rules = [(r"^https:\/\/locations\.bubbakoos\.com\/locations\/[a-z]{2}\/[\w\-]+$", "parse")]
    wanted_types = ["Restaurant"]

    def parse(self, response: TextResponse, **kwargs):
        ld_data = json.loads(
            re.search(
                r"\"({.*})\"\]", response.xpath('//*[contains(text(),"GeoCoordinates")]/text()').get().replace("\\", "")
            ).group(1)
        )
        print(ld_data)
        item = DictParser.parse(ld_data)
        item["ref"] = item["website"] = response.url
        oh = OpeningHours()
        if ld_data["openingHoursSpecification"]:
            for day_time in ld_data["openingHoursSpecification"]:
                day = day_time["dayOfWeek"]
                open_time = day_time["opens"]
                close_time = day_time["closes"]
                oh.add_range(day=day, open_time=open_time, close_time=close_time)
        item["opening_hours"] = oh
        yield item

    # def post_process_item(self, item: Feature, response: Response, ld_data: dict):
    #     item["branch"] = response.xpath("//h1/text()").get()
    #     item.pop("facebook", None)
    #     apply_category(Categories.FAST_FOOD, item)
    #     yield item
