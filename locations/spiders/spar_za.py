import scrapy

from locations.categories import Categories
from locations.dict_parser import DictParser
from locations.hours import DAYS_WEEKDAY, OpeningHours


class SparZASpider(scrapy.Spider):
    name = "spar_za"
    item_attributes = {"brand": "SPAR", "brand_wikidata": "Q610492", "extras": Categories.SHOP_SUPERMARKET.value}
    start_urls = []

    def start_requests(self):
        yield scrapy.http.JsonRequest(
            url="https://www.spar.co.za/api/stores/search",
            data={"Types": ["SPAR", "SUPERSPAR", "KWIKSPAR", "SPAR Express", "Savemor"]},
        )

    def parse(self, response, **kwargs):
        for store in response.json():
            store["lat"] = store.pop("GPSLat")
            store["lon"] = store.pop("GPSLong")
            store["name"] = store.pop("FullName")
            store["website"] = "https://www.spar.co.za/Home/Store-View/" + store.pop("Alias")
            item = DictParser.parse(store)

            oh = OpeningHours()
            for day in DAYS_WEEKDAY:
                self._add_range(oh, store, day, "TradingHoursMonToFriOpen", "TradingHoursClose")
            self._add_range(oh, store, "Sat", "TradingHoursSatOpen", "TradingHoursSatClose")
            self._add_range(oh, store, "Sun", "TradingHoursSunOpen", "TradingHoursSunClose")

            item["opening_hours"] = oh

            yield item

    @staticmethod
    def _add_range(oh: OpeningHours, store: dict, day: str, open_key: str, close_key: str):
        open_time = store[open_key]
        close_time = store[close_key]
        if open_time == "24h":
            open_time = "00h00"
            close_time = "23h59"
        if open_time and close_time:
            oh.add_range(day, open_time[:5], close_time[:5], "%Hh%M")
