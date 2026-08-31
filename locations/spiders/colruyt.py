from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.items import set_closed


class ColruytSpider(Spider):
    name = "colruyt"
    item_attributes = {"brand": "Colruyt", "brand_wikidata": "Q2363991"}
    start_urls = ["https://ecgplacesmw.colruyt.be/ecgplacesmw/v4/nl/places/searchPlaces?ensignId=8&placeTypeId=1"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json()["placeSearchDetails"]:
            item = DictParser.parse(location)
            item["branch"] = location["commercialName"].replace("COLRUYT", "").strip(" ()")

            item["lat"] = location["geoCoordinates"]["latitude"]
            item["lon"] = location["geoCoordinates"]["longitude"]
            item["ref"] = location["placeId"]
            item["website"] = location["moreInfoUrl"]

            if location["isActive"] is False:
                set_closed(item)

            apply_category(Categories.SHOP_SUPERMARKET, item)

            yield item
