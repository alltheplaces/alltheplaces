import json

from scrapy import Spider
from scrapy.http import JsonRequest

from locations.categories import Categories
from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.pipelines.address_clean_up import clean_address


class DirckIIINLSpider(Spider):
    name = "dirck_iii_nl"
    item_attributes = {"brand": "Dirck III", "brand_wikidata": "Q109188079", "extras": Categories.SHOP_ALCOHOL.value}
    allowed_domains = ["www.dirckiii.nl"]
    start_urls = ["https://www.dirckiii.nl/storelocator/index/ajax/"]

    def start_requests(self):
        for url in self.start_urls:
            yield JsonRequest(url=url)

    def parse(self, response):
        for location in response.json()["data"]:
            if not location["is_active"]:
                continue

            item = DictParser.parse(location)
            item["ref"] = location["storelocator_id"]
            item["street_address"] = clean_address(location["address"][1:])

            item["opening_hours"] = OpeningHours()
            hours_dict = json.loads(location["storetime"])
            for record in hours_dict:
                item["opening_hours"].add_range(
                    record["days"],
                    "{}:{}".format(record["open_hour"], record["open_minute"]),
                    "{}:{}".format(record["close_hour"], record["close_minute"]),
                )

            yield item
