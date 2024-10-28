import json

import scrapy

from locations.dict_parser import DictParser
from locations.hours import DAYS_FULL, OpeningHours


class SchnucksUSSpider(scrapy.Spider):
    name = "schnucks_us"
    item_attributes = {"brand": "Schnucks", "brand_wikidata": "Q7431920"}
    allowed_domains = ["locations.schnucks.com"]
    start_urls = ["https://locations.schnucks.com/"]

    def parse(self, response):
        data_raw = response.xpath('//script[@id="__NEXT_DATA__"]/text()').get()
        locations = json.loads(data_raw)["props"]["pageProps"]["locations"]
        for location in locations:
            item = DictParser.parse(location)
            item["ref"] = location["storeCode"]
            item["name"] = location["businessName"]
            item["street_address"] = location["addressLines"][0]
            item["phone"] = location["phoneNumbers"][0]
            item["website"] = location["websiteURL"]
            item["image"] = (
                "https://storage.googleapis.com/schnucks-digital-assets/storefront-image/" + item["ref"] + ".jpg"
            )
            if len(location["businessHours"]) == 7:
                oh = OpeningHours()
                for day_index in range(0, 7, 1):
                    oh.add_range(
                        DAYS_FULL[day_index],
                        location["businessHours"][day_index][0],
                        location["businessHours"][day_index][1],
                        "%H:%M",
                    )
                item["opening_hours"] = oh.as_opening_hours()
            yield item
