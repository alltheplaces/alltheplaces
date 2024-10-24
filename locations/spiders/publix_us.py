from datetime import datetime

from scrapy import Spider

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.items import set_closed


class PublixUSSpider(Spider):
    name = "publix_us"
    item_attributes = {"brand": "Publix", "brand_wikidata": "Q672170"}
    allowed_domains = ["publix.com"]
    start_urls = [
        "https://services.publix.com/storelocator/api/v1/stores/?count=3000&distance=5000&includeOpenAndCloseDates=true&city=AL&isWebsite=true"
    ]
    requires_proxy = True

    def parse(self, response, **kwargs):
        for location in response.json()["stores"]:
            if not location["isEnabled"]:
                continue

            item = DictParser.parse(location)
            item["website"] = f'https://www.publix.com/locations/{location["storeNumber"]}'
            item["phone"] = location["phoneNumbers"].get("Store")
            item["image"] = location["image"]["hero"]
            item["extras"]["start_date"] = location["openingDate"]

            if location["closingDate"]:
                set_closed(item, datetime.fromisoformat(location["closingDate"]))

            item["opening_hours"] = OpeningHours()
            for rule in location["hours"]:
                if rule["isClosed"]:
                    continue
                start_time = datetime.fromisoformat(rule["openTime"])
                end_time = datetime.fromisoformat(rule["openTime"])
                item["opening_hours"].add_range(start_time.strftime("%a"), start_time.timetuple(), end_time.timetuple())

            if location["type"] == "P":
                apply_category(Categories.PHARMACY, item)
            elif location["type"] == "R":
                apply_category(Categories.SHOP_SUPERMARKET, item)
            elif location["type"] == "W":
                item["brand"] = "Publix GreenWise Market"
                apply_category(Categories.SHOP_SUPERMARKET, item)
            else:
                self.crawler.stats.inc_value(f'atp/publix_us/unmapped_category/{location["type"]}')

            yield item
