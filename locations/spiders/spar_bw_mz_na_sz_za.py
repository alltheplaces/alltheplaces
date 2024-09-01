import scrapy

from locations.categories import Categories
from locations.dict_parser import DictParser
from locations.hours import DAYS_WEEKDAY, OpeningHours

SPAR_ZA_BRANDS = {
    "SPAR": {"brand": "SPAR", "brand_wikidata": "Q610492", "extras": Categories.SHOP_SUPERMARKET.value},
    "SUPERSPAR": {"brand": "Superspar", "brand_wikidata": "Q610492", "extras": Categories.SHOP_SUPERMARKET.value},
    "KWIKSPAR": {"brand": "KwikSpar", "brand_wikidata": "Q610492", "extras": Categories.SHOP_CONVENIENCE.value},
    "SPAR Express": {"brand": "Spar Express", "brand_wikidata": "Q610492", "extras": Categories.SHOP_CONVENIENCE.value},
    "Savemor": {"brand": "SaveMor", "brand_wikidata": "Q610492", "extras": Categories.SHOP_SUPERMARKET.value},
    "Pharmacy": {"brand": "Pharmacy at SPAR", "brand_wikidata": "Q610492", "extras": Categories.PHARMACY.value},
}


class SparBWMZNASZZASpider(scrapy.Spider):
    name = "spar_bw_mz_na_sz_za"
    start_urls = []
    skip_auto_cc_domain = True

    def start_requests(self):
        yield scrapy.http.JsonRequest(
            url="https://www.spar.co.za/api/stores/search",
            data={"Types": ["SPAR", "SUPERSPAR", "KWIKSPAR", "SPAR Express", "Savemor", "Pharmacy"]},
        )

    def parse(self, response, **kwargs):
        for store in response.json():
            store["lat"] = store.pop("GPSLat")
            store["lon"] = store.pop("GPSLong")
            store["website"] = "https://www.spar.co.za/Home/Store-View/" + store.pop("Alias")
            item = DictParser.parse(store)
            item["branch"] = item.pop("name")

            item.update(SPAR_ZA_BRANDS.get(store["Type"]))

            oh = OpeningHours()
            try:
                for day in DAYS_WEEKDAY:
                    self._add_range(oh, store, day, "TradingHoursMonToFriOpen", "TradingHoursClose")
                self._add_range(oh, store, "Sat", "TradingHoursSatOpen", "TradingHoursSatClose")
                self._add_range(oh, store, "Sun", "TradingHoursSunOpen", "TradingHoursSunClose")
            except ValueError:
                pass

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
