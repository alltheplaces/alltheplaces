from typing import Any, AsyncIterator, Iterable

from scrapy.http import JsonRequest, Response

from locations.categories import Categories, Extras, Fuel, apply_category, apply_yes_no
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class CenexSpider(JSONBlobSpider):
    name = "cenex"
    item_attributes = {"brand": "Cenex", "brand_wikidata": "Q62127191"}
    locations_key = "Locations"

    async def start(self) -> AsyncIterator[JsonRequest]:
        yield JsonRequest(
            "https://www.cenex.com/chs-sitecore/api/locationsearch/search",
            method="POST",
            data={
                "Bounds": {
                    "NorthEast": {"Latitude": 90, "Longitude": 180},
                    "SouthWest": {"Latitude": -90, "Longitude": -180},
                },
                "LocationTypes": [1, 2, 4, 8],
                "Amenities": [],
            },
        )

    def post_process_item(self, item: Feature, response: Response, feature: dict, **kwargs: Any) -> Iterable[Feature]:
        types = feature["Types"].split("|")
        if "GasStation" not in types and "PremiumDiesel" not in types:
            return  # Bulk lubricant/propane co-op dealers, not fuel stations

        item["country"] = "US"
        amenities = [a["Name"] for a in feature["Amenities"]]

        apply_category(Categories.FUEL_STATION, item)
        apply_yes_no(Extras.ATM, item, "ATM" in amenities)
        apply_yes_no(Extras.COMPRESSED_AIR, item, "Free Air" in amenities)
        apply_yes_no(Extras.CAR_WASH, item, "Car Wash" in amenities)
        apply_yes_no(Fuel.DIESEL, item, "Diesel Fuel" in amenities or "PremiumDiesel" in types)
        apply_yes_no(Fuel.HGV_DIESEL, item, "PremiumDiesel" in types)
        apply_yes_no(Fuel.ETHANOL_FREE, item, "Ethanol-free Gas" in amenities)
        apply_yes_no(Fuel.PROPANE, item, "Propane" in amenities)
        apply_yes_no(
            "food=yes",
            item,
            any(
                a in amenities
                for a in [
                    "Beer",
                    "Chicken Restaurant",
                    "Coffee Shop",
                    "Donuts",
                    "Fast Food Restaurant",
                    "Pizza Takeaway",
                    "Sandwich Shop",
                ]
            ),
        )

        yield item
