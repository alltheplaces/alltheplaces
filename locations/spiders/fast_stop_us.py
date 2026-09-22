import re
from typing import Any, AsyncIterator

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, Extras, Fuel, apply_category, apply_yes_no
from locations.items import Feature

BRAND_RE = re.compile(r"\bfast[ -]?stop( expres?s)?\b[ -]*", re.IGNORECASE)

CENTRAL_PHONES = {"888-437-3835", "641-236-3117"}

AMENITIES = {
    "ATM": Extras.ATM,
    "Air": Extras.COMPRESSED_AIR,
    "Car Wash": Extras.CAR_WASH,
    "Restroom": Extras.TOILETS,
}

FUEL_TYPES = {
    "DEF": Fuel.ADBLUE,
    "Diesel": Fuel.DIESEL,
    "E-10": Fuel.E10,
    "E-15": Fuel.E15,
    "E-85": Fuel.E85,
    "Gasoline": Fuel.GASOLINE,
    "Kerosene": Fuel.KEROSENE,
    "No Ethanol Unleaded Gas": Fuel.ETHANOL_FREE,
    "Propane Autogas": Fuel.LPG,
}


class FastStopUSSpider(Spider):
    name = "fast_stop_us"
    item_attributes = {"brand": "FAST STOP", "brand_wikidata": "Q116734101"}
    allowed_domains = ["discover.sitecorecloud.io"]
    api_url = "https://discover.sitecorecloud.io/discover/v2/129124314"
    api_key = "01-28123364-9886fa2cc5234b3d4c9d99a105d3cc653f92a1be"
    page_size = 100

    def search_request(self, offset: int) -> JsonRequest:
        return JsonRequest(
            url=self.api_url,
            headers={"Authorization": self.api_key},
            data={
                "widget": {
                    "items": [
                        {
                            "rfk_id": "rfkid_7",
                            "entity": "content",
                            "sources": ["1270972"],
                            "search": {"content": {}, "limit": self.page_size, "offset": offset},
                        }
                    ]
                },
                "context": {"locale": {"country": "us", "language": "en"}},
            },
            cb_kwargs={"offset": offset},
        )

    async def start(self) -> AsyncIterator[JsonRequest]:
        yield self.search_request(0)

    def parse(self, response: Response, offset: int = 0, **kwargs: Any) -> Any:
        widget = response.json()["widgets"][0]

        for location in widget["content"]:
            item = Feature()
            item["ref"] = location["location_id"]
            branch = re.sub(r"\s{2,}", " ", BRAND_RE.sub(" ", location["name"])).strip(" ,-")
            item["branch"] = re.sub(r"\s*\([^)]*\)$", "", branch)
            item["street_address"] = location["location_address"]
            item["city"] = location["location_city"]
            item["state"] = location["location_state"]
            item["postcode"] = location["location_zip"]
            item["country"] = "US"
            if location["location_phone"] not in CENTRAL_PHONES:
                item["phone"] = location["location_phone"]
            item["lat"] = location["location_coordinates"]["lat"]
            item["lon"] = location["location_coordinates"]["lon"]

            apply_category(Categories.FUEL_STATION, item)

            amenities = location["location_amenities"] or []
            if "24 Hour Pumps" in amenities:
                item["opening_hours"] = "24/7"
            for amenity, tag in AMENITIES.items():
                apply_yes_no(tag, item, amenity in amenities)

            fuel_types = location["location_fuel_types"] or []
            for fuel_type, tag in FUEL_TYPES.items():
                apply_yes_no(tag, item, fuel_type in fuel_types)

            yield item

        if (next_offset := offset + self.page_size) < widget["total_item"]:
            yield self.search_request(next_offset)
