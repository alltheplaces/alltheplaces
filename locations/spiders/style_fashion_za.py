from json import loads
from typing import AsyncIterator

from scrapy import Spider
from scrapy.http import JsonRequest

from locations.dict_parser import DictParser
from locations.hours import OpeningHours

COUNTRY_CODES = {
    "Botswana": "BW",
    "Namibia": "NA",
    "South Africa": "ZA",
    "Swaziland": "SZ",
}


class StyleFashionZASpider(Spider):
    name = "style_fashion_za"
    item_attributes = {"brand": "Style", "brand_wikidata": "Q130350929"}
    # Store finder is "Store Locator by Secomapp" (https://doc.storelocator.secomapp.com/)
    start_urls = ["https://stylefashion.co.za/cdn/shop/t/4/assets/sca.storelocatordata.json"]

    async def start(self) -> AsyncIterator[JsonRequest]:
        for url in self.start_urls:
            yield JsonRequest(url=url)

    def parse(self, response, **kwargs):
        for location in response.json():
            item = DictParser.parse(location)

            item["branch"] = item.pop("name", None)

            # address is a shop unit reference; address2 is the shopping centre name.
            # Neither is a street address on its own, so combine them.
            address = location.get("address", "")
            address2 = location.get("address2", "")
            if address and address2:
                item["street_address"] = f"{address}, {address2}"
            elif address or address2:
                item["street_address"] = address or address2
            item.pop("addr_full", None)

            # Map full country name to ISO 3166-1 alpha-2 code.
            country_name = location.get("country", "")
            item["country"] = COUNTRY_CODES.get(country_name, "ZA")

            # Drop all-zero placeholder postcodes.
            postcode = item.get("postcode", "")
            if postcode and not postcode.replace("0", "").strip():
                item.pop("postcode", None)

            if location.get("operating_hours"):
                item["opening_hours"] = OpeningHours()
                hours_json = loads(location["operating_hours"])
                for day_hours in hours_json.values():
                    if day_hours.get("status") != "1":
                        continue
                    for slot in day_hours.get("slot", []):
                        item["opening_hours"].add_range(
                            day_hours["name"], slot["from"], slot["to"]
                        )

            yield item
