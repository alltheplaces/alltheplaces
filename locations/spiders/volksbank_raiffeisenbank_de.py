from typing import Any, AsyncIterator

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class VolksbankRaiffeisenbankDESpider(Spider):
    name = "volksbank_raiffeisenbank_de"
    item_attributes = {"brand": "Volksbank Raiffeisenbank", "brand_wikidata": "Q1361800"}
    custom_settings = {"DEFAULT_REQUEST_HEADERS": {"token": "2MEN71Lg25DxWLysCqC94b2H"}}
    template_url = "https://api.geno-datenhub.de/places?_latitude={lat}&_longitude={lon}&kind[]={category}&_per_page=1000&_page={page}&_radius=5000000"

    async def start(self) -> AsyncIterator[JsonRequest]:
        for lat, lon in [(53.3964452, 10.4589624), (48.0927718, 10.5688257)]:
            for category in ["bank", "atm"]:
                yield JsonRequest(
                    url=self.template_url.format(category=category, page=1, lat=lat, lon=lon),
                    callback=self.parse,
                    meta=dict(page=1, category=category),
                )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for bank in response.json()["data"]:
            if "contact" in bank:
                bank["contact"]["phone"] = bank["contact"].pop("i18n_phone_number")
            bank["latitude"] = bank["address"].pop("latitude")
            bank["longitude"] = bank["address"].pop("longitude")
            item = DictParser.parse(bank)
            item["street_address"] = item.pop("street", "")
            item["website"] = bank["links"].get("detail_page_url") or bank["links"]["url"]
            item["opening_hours"] = self.parse_hours(bank["opening_hours"])
            item["extras"]["services"] = bank["services"]
            item["operator"] = bank["institute"]["name"]
            if bank["kind"] == "atm":
                apply_category(Categories.ATM, item)
            else:
                apply_category(Categories.BANK, item)
            yield item
        total_pages = response.json()["meta"]["total_pages"]
        cur_page = response.meta["page"]
        if cur_page < total_pages:
            url = self.template_url.format(
                category=response.meta["category"],
                page=cur_page + 1,
                lat=response.json()["meta"]["search_center_latitude"],
                lon=response.json()["meta"]["search_center_longitude"],
            )
            yield JsonRequest(url, callback=self.parse, meta=response.meta | {"page": cur_page + 1})

    @staticmethod
    def parse_hours(hours: dict) -> OpeningHours:
        oh = OpeningHours()
        for day, times in hours.items():
            for start_time, end_time in times:
                oh.add_range(day, start_time, end_time)
        return oh
