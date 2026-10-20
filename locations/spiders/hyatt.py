from datetime import date
from typing import AsyncIterator, Iterable

import chompjs
from scrapy import Request
from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.pipelines.address_clean_up import merge_address_lines

BRANDS = {
    "ALILA": "Q12471508",
    "ALUA": "Q126179854",
    "ANDAZ": "Q48836304",
    "CENTRIC": "Q109277705",
    "DESTINATION": "Q5265133",
    "GRAND": "Q115794899",
    "HOUSE": "Q109292191",
    "HYATT": "Q1425063",
    "PARK": "Q115794911",
    "PLACE": "Q72629292",
    "REGENCY": "Q115794868",
    "UNBOUND": "Q130293406",
    "VACATION": "Q131706454",
}


class HyattSpider(JSONBlobSpider):
    name = "hyatt"
    allowed_domains = ["www.hyatt.com"]
    start_urls = ["https://www.hyatt.com/explore-hotels"]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    async def start(self) -> AsyncIterator[Request]:
        yield Request(self.start_urls[0], meta={"zyte_api": {"browserHtml": True, "javascript": True}})

    def extract_json(self, response: TextResponse) -> list[dict]:
        hotels = []
        for region in chompjs.parse_js_object(
            response.xpath('//script[contains(text(), "window.STORE = ")]/text()').get()
        )["properties"].values():
            for sub_region in region.values():
                for country in sub_region.values():
                    for province in country.values():
                        hotels.extend(province)
        today = date.today().isoformat()
        flattened = []
        for hotel in hotels:
            # PARTNER properties are independent hotels bookable via Hyatt, e.g. Mr & Mrs Smith
            if (
                hotel["propertyType"] != "HYATT"
                or hotel["openStatus"] == "PRECONSTRUCTION_BOOKABLE"
                or (hotel["openDate"] or today) > today
            ):
                continue
            location = hotel["location"]
            # DictParser reads "region" ("North America") as the state, so drop it.
            location.pop("region")
            flattened.append(
                hotel
                | location
                | location["geolocation"]
                | {
                    "ref": hotel["spiritCode"],
                    "country": location["country"]["key"],
                    "state": (location["stateProvince"] or {}).get("label"),
                }
            )
        return flattened

    def post_process_item(self, item: Feature, response: TextResponse, hotel: dict) -> Iterable[Feature]:
        item["street_address"] = merge_address_lines([hotel["addressLine1"], hotel["addressLine2"]])
        if hotel["image"].startswith("https://"):
            item["image"] = hotel["image"]
        if brand := hotel["brand"]["label"]:
            item["brand"] = brand
            item["brand_wikidata"] = BRANDS.get(hotel["brand"]["key"])
        apply_category(Categories.HOTEL, item)
        yield item
