import re

from scrapy import Spider

from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class SallyBeautyGBSpider(Spider):
    name = "sally_beauty_gb"
    item_attributes = {"brand": "Sally Beauty", "brand_wikidata": "Q7405065"}
    start_urls = [
        "https://www.sallybeauty.co.uk/on/demandware.store/Sites-sally-beauty-Site/en_GB/Stores-GetStoresJSON"
    ]

    def parse(self, response, **kwargs):
        for store in response.json():
            store["address"] = store.pop("formattedAddress")

            item = DictParser.parse(store)
            item["branch"] = item.pop("name")
            item["website"] = "https://www.sallybeauty.co.uk/storeinfo?StoreID=" + store["ID"]
            item["country"] = item["addr_full"][-2:]

            if store["hours"]:
                oh = OpeningHours()
                for day, open_time, close_time in re.findall(
                    r"(\w{3}): ([\d.]+(?:am|pm)) - ([\d.]+(?:am|pm))", store["hours"]
                ):
                    oh.add_range(day, open_time, close_time, time_format="%I.%M%p")
                item["opening_hours"] = oh

            yield item
