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
        "https://services.publix.com/storelocator/api/v1/stores/?count=3000&distance=5000&includeOpenAndCloseDates=true&isWebsite=true&latitude=39.8422945&longitude=-74.8828235"
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

            if location["openingDate"]:
                item["extras"]["start_date"] = location["openingDate"].split("T", 1)[0]
            if location["closingDate"]:
                set_closed(item, datetime.fromisoformat(location["closingDate"]))

            for secondary in location["secondaryLocations"]:
                i = item.deepcopy()
                i["ref"] = "{}-{}".format(item["ref"], secondary["type"])
                i["phone"] = secondary["phone"]
                i["opening_hours"] = self.parse_opening_hours(secondary["hours"])

                if secondary["type"] == "P":
                    i["name"] = None
                    apply_category(Categories.PHARMACY, i)
                elif secondary["type"] == "L":
                    i["name"] = "Publix Liquors"
                    apply_category(Categories.SHOP_ALCOHOL, i)
                else:
                    self.logger.error("Unrecognised type: {}".format(location["type"]))
                    self.crawler.stats.inc_value(f'atp/publix_us/unmapped_category/{location["type"]}')

                yield i

            item["opening_hours"] = self.parse_opening_hours(location["hours"])

            if location["type"] == "P":
                item["branch"] = item.pop("name").removeprefix("Publix Pharmacy at ")
                apply_category(Categories.PHARMACY, item)
            elif location["type"] == "R":
                item["branch"] = item.pop("name").removeprefix("Publix ").removeprefix("Super Market ")
                apply_category(Categories.SHOP_SUPERMARKET, item)
            elif location["type"] == "W":
                item["name"] = "Publix GreenWise Market"
                apply_category(Categories.SHOP_SUPERMARKET, item)
            else:
                self.logger.error("Unrecognised type: {}".format(location["type"]))
                self.crawler.stats.inc_value(f'atp/publix_us/unmapped_category/{location["type"]}')

            yield item

    def parse_opening_hours(self, hours: list[dict]) -> OpeningHours:
        oh = OpeningHours()
        for rule in hours:
            if rule["isClosed"]:
                continue
            start_time = datetime.fromisoformat(rule["openTime"])
            end_time = datetime.fromisoformat(rule["openTime"])
            oh.add_range(start_time.strftime("%a"), start_time.timetuple(), end_time.timetuple())
        return oh
