import json

import scrapy

from locations.hours import OpeningHours
from locations.items import GeojsonPointItem


class BrewdogSpider(scrapy.Spider):
    name = "brewdog"
    item_attributes = {"brand": "BrewDog", "brand_wikidata": "Q911367"}
    allowed_domains = ["www.brewdog.com"]
    start_urls = ["https://www.brewdog.com/uk/bar-locator#ALL"]

    def parse(self, response):
        data = response.xpath('//script[@id="__NEXT_DATA__"]/text()').get()
        data_json = json.loads(data)
        bars = data_json["props"]["pageProps"]["content"]
        item = GeojsonPointItem()
        for bar in bars:
            item["ref"] = bar["sys"].get("id")
            item["name"] = bar["fields"].get("name")
            item["addr_full"] = bar["fields"].get("address")
            item["phone"] = bar["fields"].get("contactNumber")
            item["email"] = bar["fields"].get("contactEmail")
            item["lat"] = bar["fields"].get("location", {}).get("lat")
            item["lon"] = bar["fields"].get("location", {}).get("lon")
            openingHours = bar["fields"].get("openingHours")
            oh = OpeningHours()
            if openingHours:
                for key, value in openingHours.items():
                    if key == "exceptions" or value["is_open"] is False:
                        continue
                    oh.add_range(
                        day=key,
                        open_time=value.get("open"),
                        close_time=value.get("close"),
                    )
            item["opening_hours"] = oh.as_opening_hours()
            yield item
