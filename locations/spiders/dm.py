import scrapy

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours


class DmSpider(scrapy.Spider):
    name = "dm"
    item_attributes = {"brand": "dm", "brand_wikidata": "Q266572"}
    start_urls = [
        "https://store-data-service.services.dmtech.com/stores/bbox/49.27562530004775%2C10.195245519081993%2C47.019140477949975%2C24.043815030918438",
        "https://store-data-service.services.dmtech.com/stores/bbox/53.81734501171468%2C-0.8184878281186911%2C46.98695695433199%2C16.603367890508224",
        "https://store-data-service.services.dmtech.com/stores/bbox/47.786865948031554,14.70566557769028,42.709273836666,24.75120274749999",
        "https://store-data-service.services.dmtech.com/stores/bbox/47.786865948031554,14.70566557769028,45.21501355698323,16.19156309497206",
        "https://store-data-service.services.dmtech.com/stores/bbox/47.786865948031554,14.70566557769028,41.78413678399999,21.484047576",
    ]

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
            if location.get("openingHours"):
                item["opening_hours"] = self.parse_hours(location.get("openingHours"))

            apply_category(Categories.SHOP_CHEMIST, item)

            yield item
