import scrapy

from locations.hours import OpeningHours
from locations.linked_data_parser import LinkedDataParser


class WaffleHouseSpider(scrapy.Spider):
    name = "wafflehouse"
    item_attributes = {"brand": "Waffle House", "brand_wikidata": "Q1701206"}
    allowed_domains = ["wafflehouse.com"]
    start_urls = ["https://locations.wafflehouse.com/regions"]

    def parse(self, response):
        yield from response.follow_all(css="div.tiles a")

        ld = LinkedDataParser.find_linked_data(response, "LocalBusiness")
        if ld is not None:
            oh = OpeningHours()
            oh.from_linked_data(ld, "%I%p")
            item = LinkedDataParser.parse_ld(ld)
            item["opening_hours"] = oh.as_opening_hours()
            yield item
