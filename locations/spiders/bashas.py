import html
import json

import scrapy

from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class BashasSpider(scrapy.spiders.SitemapSpider):
    name = "bashas"
    item_attributes = {
        "brand": "Bashas'",
        "brand_wikidata": "Q4866786",
    }

    download_delay = 0.2
    sitemap_urls = ["https://www.bashas.com/wpsl_stores-sitemap.xml"]
    sitemap_rules = [("/stores/", "parse_store")]

    def parse_store(self, response):
        script = response.xpath("//script[@id='wpsl-js-js-extra']/text()").extract_first()
        open_brace = script.find('"locations":[{') + 13
        close_brace = script.rfind("}]}") + 1
        store_json = json.loads(script[open_brace:close_brace])
        hours = response.xpath("//table[@class='wpsl-opening-hours']//text()").extract()

        item = DictParser.parse(store_json)
        item["street_address"] = item.pop("addr_full", None)
        item["country"] = "US"
        item["name"] = html.unescape(store_json["store"])
        item["website"] = response.url
        item["phone"] = response.xpath("//div[@class='wpsl-contact-details']//text()").extract()[1]
        item["opening_hours"] = self.parse_hours(hours)

        yield item

    @staticmethod
    def parse_hours(hours):
        opening_hours = OpeningHours()

        days = hours[0::2]
        times = hours[1::2]

        for day, time_range in zip(days, times):
            open_time, close_time = time_range.split(" - ")
            opening_hours.add_range(day=day[0:2], open_time=open_time, close_time=close_time, time_format="%I:%M %p")

        return opening_hours
