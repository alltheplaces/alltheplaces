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
            item["ref"] = bar["sys"]["id"]
            item["name"] = bar["fields"]["name"]
            item["addr_full"] = bar["fields"]["address"] if "address" in bar["fields"].keys() else None
            item["phone"] = bar["fields"]["contactNumber"] if "contactNumber" in bar["fields"].keys() else None
            item["email"] = bar["fields"]["contactEmail"] if "contactEmail" in bar["fields"].keys() else None
            item["lat"] = bar["fields"]["location"]["lat"] if "location" in bar["fields"].keys() else None
            item["lon"] = bar["fields"]["location"]["lon"] if "location" in bar["fields"] else None
            openingHours = bar["fields"]["openingHours"] if "openingHours" in bar["fields"].keys() else None
            oh = OpeningHours()
            if openingHours:
                for key, value in openingHours.items():
                    if key == "exceptions" or value["is_open"] == False:
                        continue
                    if "open" and "close" in value.keys():
                        oh.add_range(
                            day=key,
                            open_time=value["open"],
                            close_time=value["close"],
                        )
            item["opening_hours"] = oh.as_opening_hours()
            yield item
