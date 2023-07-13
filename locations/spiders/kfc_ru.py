import scrapy
from scrapy.http import JsonRequest

from locations.categories import apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import DAYS_EN, OpeningHours


class KfcRUSpider(scrapy.Spider):
    name = "kfc_ru"
    allowed_domains = ["kfc.digital"]
    item_attributes = {"brand": "KFC", "brand_wikidata": "Q524757"}

    def start_requests(self):
        yield JsonRequest("https://api.kfc.digital/api/store/v2/store.get_restaurants?showClosed=false")

    def parse(self, response):
        for poi in response.json().get("searchResults"):
            store = poi.get("storePublic")
            if store.get("brand") != "kfc":
                # TODO: add Rostics (https://xn--h1aekhgce.xn--p1ai/) to NSI/Wikidata,
                #       it will slowly replace KFC in RU
                continue
            item = DictParser.parse(store)
            item["ref"] = store.get("storeId")
            item["name"] = store.get("title", {}).get("ru")
            item["extras"]["name:en"] = store.get("title", {}).get("en")
            # There are a few test stores in the data, skip them
            if item["name"].lower().startswith("тест"):
                continue
            contacts = store.get("contacts")
            item["phone"] = contacts.get("phoneNumber")
            item["addr_full"] = contacts.get("streetAddress", {}).get("ru")
            item["city"] = contacts.get("city", {}).get("ru")
            lat, lon = contacts.get("coordinates", {}).get("geometry", {}).get("coordinates", [])
            item["lat"] = lat
            item["lon"] = lon
            self.parse_hours(item, store)
            apply_yes_no("drive_through", item, "driveIn" in store.get("features", []))
            apply_yes_no("internet_access=wlan", item, "wifi" in store.get("features", []))
            yield item

    def parse_hours(self, item, store):
        if hours := store.get("openingHours"):
            try:
                oh = OpeningHours()
                daily = hours.get("regularDaily")
                for day in daily:
                    oh.add_range(
                        DAYS_EN.get(day.get("weekDayName")), day.get("timeFrom"), day.get("timeTill"), "%H:%M:%S"
                    )
                item["opening_hours"] = oh.as_opening_hours()
            except:
                self.logger.info(f"Bad format for opening hours {hours}")
