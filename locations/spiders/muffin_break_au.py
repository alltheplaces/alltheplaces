import scrapy

from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class MuffinBreakAUSpider(scrapy.Spider):
    name = "muffin_break_au"
    item_attributes = {"brand": "Muffin Break", "brand_wikidata": "Q16964876"}
    allowed_domains = ["muffinbreak.com.au"]
    start_urls = ["https://muffinbreak.com.au/wp-json/store-locator/v1/store/"]

    def parse(self, response):
        for location in response.json():
            item = DictParser.parse(location)
            item["name"] = location["locname"].replace("&#8217;", "’")
            item["addr_full"] = location["address"].strip()
            if len(location["address2"].strip()) > 0:
                item["addr_full"] = item["addr_full"] + ", " + location["address2"].strip()
            item["website"] = location["web"]
            yield scrapy.Request(item["website"], meta={"item": item}, callback=self.parse_hours)

    def parse_hours(self, response):
        item = response.meta["item"]
        oh = OpeningHours()
        hours_raw = (
            (" ".join(response.xpath('//table[contains(@class, "c-table")]/tr/td/text()').getall()))
            .replace("Open 7 Days", "Mo-Su")
            .replace("Thuesday", "Thursday")
            .replace("8:300pm", "8:30pm")
        )
        oh.add_ranges_from_string(hours_raw)
        item["opening_hours"] = oh.as_opening_hours()
        yield item
