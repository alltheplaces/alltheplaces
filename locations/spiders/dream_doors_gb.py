import re
from typing import Any

from scrapy.http import Response
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.hours import OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines


class DreamDoorsGBSpider(CrawlSpider):
    name = "dream_doors_gb"
    item_attributes = {"brand": "Dream Doors", "brand_wikidata": "Q84702301"}
    start_urls = ["https://www.dreamdoors.co.uk/kitchen-showrooms"]
    rules = [Rule(LinkExtractor(allow=[r"https://www.dreamdoors.co.uk/kitchen-showrooms/[^/]+$"]), callback="parse")]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        item = Feature()
        item["ref"] = item["website"] = response.url
        item["addr_full"] = merge_address_lines(response.xpath('//div[@class="address"]/p/text()').getall())
        item["phone"] = response.xpath('//a[@id="showroom-phone"]/text()').get()

        item["opening_hours"] = OpeningHours()
        for rule in response.xpath('//div[@class="opening_times"]/div[@class="day"]'):
            day = rule.xpath("./p[1]/text()").get()
            times = rule.xpath("./p[2]/text()").get().replace(".", ":")
            if times == "Closed":
                item["opening_hours"].set_closed(day)
            else:
                start_time, end_time = times.replace("-", "–").split("–")
                if ":" not in start_time:
                    start_time = start_time.replace("am", ":00am")
                if ":" not in end_time:
                    end_time = end_time.replace("pm", ":00pm")
                item["opening_hours"].add_range(day, start_time.strip(), end_time.strip(), "%I:%M%p")

        if m := re.search(
            r'map_initialize\("map_canvas",\s*"(.+?)",\s*(-?\d+\.\d+),\s*(-?\d+\.\d+)\s*\);',
            response.text,
        ):
            _, item["lat"], item["lon"] = m.groups()

        yield item
