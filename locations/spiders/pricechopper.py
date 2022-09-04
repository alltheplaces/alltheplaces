# -*- coding: utf-8 -*-
import scrapy
from scrapy.spiders import Rule
from scrapy.linkextractors import LinkExtractor


from locations.hours import OpeningHours
from locations.linked_data_parser import LinkedDataParser


class PriceChopperSpider(scrapy.spiders.CrawlSpider):
    name = "pricechopper"
    item_attributes = {"brand_wikidata": "Q7242574"}
    allowed_domains = ["pricechopper.com"]
    start_urls = ["https://www.pricechopper.com/stores/"]
    rules = [
        Rule(LinkExtractor(allow=r"/stores/.*\.html$"), callback="parse"),
        Rule(LinkExtractor(allow=r"/stores/")),
    ]

    def parse(self, response):
        item = LinkedDataParser.parse(response, "GroceryStore")
        item["ref"] = response.url.removesuffix(".html").rsplit("-", 1)[-1]
        item["brand"] = response.xpath("//@data-brand").get()

        oh = OpeningHours()
        for row in response.css("[data-hours-type=primary] .day-hour-row"):
            day = row.css(".daypart::text").get().strip()[:2]
            open_time = row.css(".time-open::text").get()
            close_time = row.css(".time-close::text").get()
            oh.add_range(day, open_time, close_time, "%I%p")
        item["opening_hours"] = oh.as_opening_hours()

        yield item
