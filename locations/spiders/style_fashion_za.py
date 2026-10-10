import re
from json import loads
from typing import Any
from urllib.parse import urljoin

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
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
    start_urls = ["https://stylefashion.co.za/pages/store-locator"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        asset_url = response.urljoin(
            response.xpath('(//@href | //@src)[contains(., "/cdn/shop/t/") and contains(., "/assets/")]').get()
        )
        yield JsonRequest(url=urljoin(asset_url, "sca.storelocatordata.json"), callback=self.parse_locations)

    def parse_locations(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json():
            item = DictParser.parse(location)

            item["country"] = COUNTRY_CODES.get(location.get("country"), "ZA")

            item["branch"] = re.sub(r"^(?:BW|NA|SW)\s+|\s*\([A-Z]\d+\)$", "", item.pop("name", "")).strip() or None

            address_parts = [
                re.sub(r"^Style\b\s*", "", part or "").strip()
                for part in (location.get("address"), location.get("address2"))
            ]
            item["street_address"] = ", ".join(part for part in address_parts if part)
            item.pop("addr_full", None)

            if (postcode := item.get("postcode")) and not postcode.strip("0"):
                item.pop("postcode")

            if location.get("operating_hours"):
                item["opening_hours"] = OpeningHours()
                for day_hours in loads(location["operating_hours"]).values():
                    if day_hours["status"] == "1":
                        for slot in day_hours["slot"]:
                            item["opening_hours"].add_range(day_hours["name"], slot["from"], slot["to"])
                    else:
                        item["opening_hours"].set_closed(day_hours["name"])

            apply_category(Categories.SHOP_CLOTHES, item)

            yield item
