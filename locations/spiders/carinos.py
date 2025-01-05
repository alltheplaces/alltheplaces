import json

import scrapy

from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class CarinosSpider(scrapy.Spider):
    name = "carinos"
    item_attributes = {"brand": "Carino's Italian", "brand_wikidata": "Q5039637"}
    allowed_domains = ["carinos.com"]
    start_urls = ["https://www.carinos.com/locations/#/"]

    def find_between(self, text, first, last):
        start = text.index(first) + len(first)
        end = text.index(last, start)
        return text[start:end]

    def parse(self, response):
        for data in json.loads(f'{self.find_between(response.text, "carinos.locations.list = ", "];")}]'):
            yield scrapy.Request(
                url=f'https://www.{self.allowed_domains[0]}{data.get("url")}',
                callback=self.parse_store,
                cb_kwargs={"data": data},
            )

    def parse_store(self, response, data):
        days = response.xpath('//div[@class="group-hour-day"]')

        oh = OpeningHours()
        for day in days:
            oh.add_range(
                day=day.xpath("./div/text()").get(),
                open_time=day.xpath(".//li/text()").get().strip().split(" - ")[0],
                close_time=day.xpath(".//li/text()").get().strip().split(" - ")[1],
                time_format="%I:%M%p",
            )

        item = DictParser.parse(data)
        item["website"] = response.url
        item["opening_hours"] = oh.as_opening_hours()

        item["street_address"] = item.pop("addr_full", None)
        yield item
