from typing import AsyncIterator
from urllib.parse import urlencode

from scrapy import Spider
from scrapy.http import JsonRequest

from locations.categories import Categories, apply_category
from locations.hours import DAYS, OpeningHours
from locations.items import Feature


class SearsUSSpider(Spider):
    name = "sears_us"
    item_attributes = {"brand": "Sears", "brand_wikidata": "Q6499202"}
    allowed_domains = ["www.sears.com"]
    start_urls = ["https://www.sears.com/stores.html"]
    handle_httpstatus_list = [404]
    custom_headers = {"Authorization": "SEARS"}
    search_zip_codes = [
        "00501",
        "00601",
        "00725",
        "00802",
        "00820",
        "00918",
        "01040",
        "02108",
        "02903",
        "04101",
        "05401",
        "06103",
        "07030",
        "10001",
        "10101",
        "12207",
        "14202",
        "15219",
        "17101",
        "19103",
        "20001",
        "21201",
        "23219",
        "27601",
        "29201",
        "30303",
        "32801",
        "33101",
        "33134",
        "33602",
        "35203",
        "37219",
        "39201",
        "40202",
        "43215",
        "46204",
        "48226",
        "48933",
        "53202",
        "55101",
        "55401",
        "60601",
        "62701",
        "64106",
        "65101",
        "70112",
        "70802",
        "72201",
        "73102",
        "75201",
        "77002",
        "78701",
        "80202",
        "84101",
        "85001",
        "87102",
        "89101",
        "90001",
        "91502",
        "94102",
        "95814",
        "96813",
        "96910",
        "96913",
        "96929",
        "98101",
        "99501",
    ]

    async def start(self) -> AsyncIterator[JsonRequest]:
        for zip_code in self.search_zip_codes:
            query = urlencode(
                {
                    "store": "Sears",
                    "mileRadius": "200",
                    "caller": "storeLocator",
                    "includeFilterStrTypes": "002_A|002_B|001_O|001_A|001_B|001_C|001_D",
                    "zipCode": zip_code,
                }
            )
            yield JsonRequest(
                url=f"https://www.sears.com/api/sal/v1/store/stores?{query}",
                headers=self.custom_headers,
                callback=self.parse,
            )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.seen_refs = set()

    def parse(self, response):
        if response.status == 404:
            return

        for store in response.json().get("stores", []):
            if store.get("isActive") != "1":
                continue
            if "sears" not in store.get("siteId", []):
                continue
            if store["storeNumber"] in self.seen_refs:
                continue
            self.seen_refs.add(store["storeNumber"])

            address = store["address"]
            item = Feature(
                ref=store["storeNumber"],
                name="Sears",
                branch=store["name"].title(),
                lat=store["latitude"],
                lon=store["longitude"],
                street_address=address.get("address1"),
                city=address.get("city"),
                state=address.get("stateCode"),
                postcode=address.get("zipCode"),
                country=address.get("country"),
                phone=address.get("contactNumbers", [None])[0],
                website=self.start_urls[0],
                opening_hours=self.parse_hours(store.get("hours")),
            )
            apply_category(Categories.SHOP_DEPARTMENT_STORE, item)
            yield item

    @staticmethod
    def parse_hours(hours: dict | None) -> OpeningHours | None:
        if not hours:
            return None

        opening_hours = OpeningHours()
        for day_number, day_name in enumerate(["mon", "tue", "wed", "thu", "fri", "sat", "sun"]):
            if day_name not in hours:
                continue

            open_time = SearsUSSpider.seconds_to_time(hours[day_name].get("openTime"))
            close_time = SearsUSSpider.seconds_to_time(hours[day_name].get("closeTime"))
            if open_time and close_time:
                opening_hours.add_range(DAYS[day_number], open_time, close_time)

        return opening_hours if opening_hours.as_opening_hours() else None

    @staticmethod
    def seconds_to_time(seconds: str | None) -> str | None:
        if seconds is None:
            return None

        seconds = int(seconds)
        return f"{seconds // 3600:02d}:{seconds % 3600 // 60:02d}"
