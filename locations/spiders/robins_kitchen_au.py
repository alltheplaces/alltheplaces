from typing import AsyncIterator

from scrapy import Spider
from scrapy.http import Request

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.pipelines.address_clean_up import clean_address


class RobinsKitchenAUSpider(Spider):
    name = "robins_kitchen_au"
    item_attributes = {
        "brand": "Robins Kitchen",
        "brand_wikidata": "Q126175864",
    }
    allowed_domains = ["www.robinskitchen.com.au"]
    start_urls = ["https://www.robinskitchen.com.au/api/get-stores"]

    async def start(self) -> AsyncIterator[Request]:
        for url in self.start_urls:
            yield Request(url=url, method="POST")

    def parse(self, response):
        for location in response.json():
            item = DictParser.parse(location)

            item["branch"] = item["name"].replace("Robins Kitchen ", "")
            item["geometry"] = location["location"]
            item["street_address"] = clean_address([location["address1"], location["address2"]])
            item["website"] = "https://www.robinskitchen.com.au/stores/" + location["slug"]

            item["opening_hours"] = OpeningHours()
            for day_name, hours in location["storeHours"].items():
                if hours["open"] == "-" or hours["close"] == "-":
                    continue
                item["opening_hours"].add_range(
                    day_name.title(),
                    hours["open"].replace(".", ":").strip(),
                    hours["close"].replace(".", ":").replace(":-", ":").strip(),
                )

            apply_category(Categories.SHOP_HOUSEWARE, item)
            yield item
