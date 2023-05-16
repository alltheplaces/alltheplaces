import re

import scrapy

from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours


class FiestaMartUSSpider(scrapy.Spider):
    name = "fiesta_mart_us"
    item_attributes = {"brand": "Fiesta Mart", "brand_wikidata": "Q5447326"}
    allowed_domains = ["fiestamart.com"]
    start_urls = ["https://www.fiestamart.com/wp-json/fiesta/v1/stores"]

    def parse(self, response):
        for data in response.json():
            item = DictParser.parse(data)
            item["state"] = (re.findall("[A-Z]{2}", item["addr_full"])[:1] or (None,))[-1]
            item["postcode"] = re.findall("[0-9]{5}$|[A-Z0-9]{3} [A-Z0-9]{3}$", item["addr_full"])[-1]
            item["ref"] = (re.findall("[0-9]+", item["website"])[:1] or (None,))[0]
            item["city"] = re.findall(", [a-zA-Z ]+,", item["addr_full"])[0].replace(",", "").strip()
            item["street_address"] = (
                item["addr_full"]
                .replace(item["city"], "")
                .replace(item["postcode"], "")
                .replace(item["state"], "")
                .replace(",", "")
            ).strip()
            oh = OpeningHours()
            for day in DAYS:
                if not data.get("hours"):
                    continue
                oh.add_range(
                    day=day,
                    open_time=re.split(" - |-", data.get("hours"))[0],
                    close_time=re.split(" - |-", data.get("hours"))[1],
                    time_format="%I:%M %p",
                )
            item["opening_hours"] = oh.as_opening_hours()

            yield item
