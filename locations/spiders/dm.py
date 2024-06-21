import scrapy

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours


class DmSpider(scrapy.Spider):
    name = "dm"
    item_attributes = {"brand": "dm", "brand_wikidata": "Q266572"}
    allowed_domains = ["store-data-service.services.dmtech.com"]
    start_urls = ["https://store-data-service.services.dmtech.com/stores/bbox/89.999,-179.999,-89.999,179.999"]

    @staticmethod
    def parse_hours(store_hours: list[dict]) -> OpeningHours:
        opening_hours = OpeningHours()

        for store_day in store_hours:
            for times in store_day["timeRanges"]:
                open_time = times["opening"]
                close_time = times["closing"]

                opening_hours.add_range(DAYS[store_day["weekDay"] - 1], open_time, close_time)

        return opening_hours

    def parse(self, response, **kwargs):
        for location in response.json()["stores"]:
            location["address"]["street_address"] = location["address"].pop("street")
            location["address"]["country"] = location["countryCode"]
            item = DictParser.parse(location)
            if location["countryCode"] in ["BG", "BA", "IT"]:
                item["website"] = (
                    f'https://www.dm-drogeriemarkt.{location["countryCode"].lower()}/store{location["storeUrlPath"]}'
                )
            elif location["countryCode"] == "SK":
                item["website"] = f'https://www.mojadm.sk/store{location["storeUrlPath"]}'
            else:
                item["website"] = f'https://www.dm.{location["countryCode"].lower()}/store{location["storeUrlPath"]}'
            item["extras"]["check_date"] = location["updateTimeStamp"]
            item["opening_hours"] = self.parse_hours(location["openingHours"])

            apply_category(Categories.SHOP_CHEMIST, item)

            yield item
