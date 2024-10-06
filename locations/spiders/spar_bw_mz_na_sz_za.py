from typing import Iterable

from scrapy.http import JsonRequest, Response

from locations.categories import Categories
from locations.hours import DAYS_WEEKDAY, OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider

SPAR_ZA_BRANDS = {
    "SPAR": {"brand": "SPAR", "brand_wikidata": "Q610492", "extras": Categories.SHOP_SUPERMARKET.value},
    "SUPERSPAR": {"brand": "Superspar", "brand_wikidata": "Q610492", "extras": Categories.SHOP_SUPERMARKET.value},
    "KWIKSPAR": {"brand": "KwikSpar", "brand_wikidata": "Q610492", "extras": Categories.SHOP_CONVENIENCE.value},
    "SPAR Express": {"brand": "Spar Express", "brand_wikidata": "Q610492", "extras": Categories.SHOP_CONVENIENCE.value},
    "Savemor": {"brand": "SaveMor", "brand_wikidata": "Q610492", "extras": Categories.SHOP_SUPERMARKET.value},
    "Pharmacy": {"brand": "Pharmacy at SPAR", "brand_wikidata": "Q610492", "extras": Categories.PHARMACY.value},
}


class SparBWMZNASZZASpider(JSONBlobSpider):
    download_timeout = 30
    name = "spar_bw_mz_na_sz_za"
    start_urls = []
    skip_auto_cc_domain = True

    def start_requests(self):
        yield JsonRequest(
            url="https://www.spar.co.za/api/stores/search",
            data={"Types": ["SPAR", "SUPERSPAR", "KWIKSPAR", "SPAR Express", "Savemor", "Pharmacy"]},
        )

    def post_process_item(self, item: Feature, response: Response, location: dict) -> Iterable[Feature]:
        item["website"] = "https://www.spar.co.za/Home/Store-View/" + location.pop("Alias")
        item["branch"] = item.pop("name")
        if item.get("addr_full") is not None:
            item["street_address"] = item.pop("addr_full")

        item.update(SPAR_ZA_BRANDS.get(location["Type"]))

        item["opening_hours"] = OpeningHours()
        try:
            for day in DAYS_WEEKDAY:
                self._add_range(item["opening_hours"], location, day, "TradingHoursMonToFriOpen", "TradingHoursClose")
            self._add_range(item["opening_hours"], location, "Sat", "TradingHoursSatOpen", "TradingHoursSatClose")
            self._add_range(item["opening_hours"], location, "Sun", "TradingHoursSunOpen", "TradingHoursSunClose")
        except ValueError:
            pass

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
