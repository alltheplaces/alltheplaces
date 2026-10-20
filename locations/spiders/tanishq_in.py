import string
from typing import Any, Iterable
from urllib.parse import quote

import scrapy
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS, OpeningHours
from locations.items import Feature

SEARCH_URL = "https://stores.tanishq.co.in/stores/tanishq/searchCity?value={}"
DETAILS_URL = "https://stores.tanishq.co.in/stores/tanishq/details?storeCode=&city={}"


class TanishqINSpider(scrapy.Spider):
    name = "tanishq_in"
    item_attributes = {"brand": "Tanishq", "brand_wikidata": "Q13117711"}
    allowed_domains = ["stores.tanishq.co.in"]
    # The search endpoint matches a substring against city, address, store name
    # and pincode, so sweeping the alphabet reaches every store regardless of
    # which cities exist.
    start_urls = [SEARCH_URL.format(letter) for letter in string.ascii_lowercase]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.seen_cities = set()

    def parse(self, response: Response) -> Iterable[scrapy.Request]:
        payload = response.json()
        if not isinstance(payload.get("result"), list):
            self.logger.warning("No results for %s: %s", response.url, payload.get("message"))
            return
        for store in payload["result"]:
            city = (store.get("city") or "").strip()
            if not city or city.casefold() in self.seen_cities:
                continue
            self.seen_cities.add(city.casefold())
            yield JsonRequest(url=DETAILS_URL.format(quote(city)), callback=self.parse_city)

    def parse_city(self, response: Response) -> Iterable[Feature]:
        payload = response.json()
        if not isinstance(payload.get("result"), list):
            self.logger.warning("No results for %s: %s", response.url, payload.get("message"))
            return
        for location in payload["result"]:
            item = Feature()
            item["ref"] = location["storeCode"]
            item["branch"] = self.branch_name(location)
            item["addr_full"] = location.get("storeAddress")
            item["city"] = location.get("storeCity")
            item["state"] = location.get("storeState")
            item["postcode"] = location.get("storeZipCode")
            item["country"] = location.get("storeCountry")
            item["lat"] = location.get("storeLatitude")
            item["lon"] = location.get("storeLongitude")
            item["phone"] = self.clean_phone(location.get("storePhoneNoOne"))
            item["email"] = location.get("storeEmailId")
            item["opening_hours"] = self.parse_hours(location)
            apply_category(Categories.SHOP_JEWELRY, item)
            yield item

    @staticmethod
    def branch_name(location: dict[str, Any]) -> str | None:
        name = (location.get("storeName") or "").strip()
        city = (location.get("storeCity") or "").strip()
        if city and name.casefold().startswith(f"{city.casefold()} -"):
            name = name[len(city) + 2 :].strip()
        return name or None

    def parse_hours(self, location: dict[str, Any]) -> OpeningHours | None:
        open_time = (location.get("storeOpeningTime") or "").strip()
        close_time = (location.get("storeClosingTime") or "").strip()
        if not open_time or not close_time:
            return None
        hours = OpeningHours()
        try:
            hours.add_days_range(DAYS, open_time, close_time, time_format="%I.%M.%S %p")
        except ValueError:
            self.logger.warning("Unrecognised hours: %s - %s", open_time, close_time)
            return None
        return hours

    @staticmethod
    def clean_phone(phone: str | None) -> str | None:
        phone = (phone or "").strip()
        # Some source records are mangled into scientific notation, eg "6.47E+09".
        if sum(character.isdigit() for character in phone) < 6 or "E+" in phone.upper():
            return None
        return phone
