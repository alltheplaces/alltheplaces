from typing import Any, Iterable

from scrapy import Request, Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Access, Categories, Extras, Fuel, apply_category, apply_yes_no
from locations.items import Feature
from locations.spiders.seven_eleven_au import SEVEN_ELEVEN_SHARED_ATTRIBUTES

PREEM = {"brand": "Preem", "brand_wikidata": "Q598835"}
UNOX = {"brand": "Uno-X", "brand_wikidata": "Q3362746"}
YX = {"brand": "YX", "brand_wikidata": "Q4580519"}


class XySpider(Spider):
    name = "xy"

    def start_requests(self) -> Iterable[Request]:
        yield JsonRequest(
            url="https://meilisearch.yx.no/indexes/stations/search",
            headers={"X-Meili-API-Key": "cda56406d550585ce01807040c54ad1614aca7bc81e42d9872633b3c194eeabe"},
            data={
                "facetsDistribution": ["tags", "chain", "fuel", "other"],
                "attributesToHighlight": ["*"],
                "limit": 2000,
                "q": "",
            },
        )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json()["hits"]:
            item = Feature()
            item["ref"] = item["extras"]["ref:yx"] = location["site"]
            item["lat"] = location["_geo"]["lat"]
            item["lon"] = location["_geo"]["lng"]
            item["name"] = location["name"]
            item["street_address"] = location["address"]
            item["postcode"] = location["zipcode"]
            item["country"] = location["country"]
            item["email"] = location["email"]
            item["phone"] = location["phone"]

            if location["chain"] == "Preem":
                item.update(PREEM)
                item["name"] = None
                apply_category(Categories.FUEL_STATION, item)
            elif location["chain"] == "YX":
                item.update(YX)
                item["branch"] = item.pop("name").removeprefix("YX ")
                apply_category(Categories.FUEL_STATION, item)
            elif location["chain"] == "YX 711":
                item.update(SEVEN_ELEVEN_SHARED_ATTRIBUTES)
                item["branch"] = item.pop("name").removeprefix("YX ").removeprefix("7-Eleven ")
                apply_category(Categories.SHOP_CONVENIENCE, item)
            elif location["chain"] == "YX Truck":
                item.update(YX)
                item["name"] = "YX Truck"
                apply_category(Categories.FUEL_STATION, item)
            elif location["chain"] == "Uno-X":
                item.update(UNOX)
                item["branch"] = item.pop("name").removeprefix("Uno-X ")
                apply_category(Categories.FUEL_STATION, item)

            apply_yes_no(Fuel.ADBLUE, item, "adblue" in location["fuel"])
            apply_yes_no(Fuel.DIESEL, item, "diesel" in location["fuel"])
            # apply_yes_no(, item, "diesel-colored" in location["fuel"])
            apply_yes_no(Fuel.OCTANE_95, item, "gasoline95" in location["fuel"])
            apply_yes_no(Fuel.OCTANE_98, item, "gasoline98" in location["fuel"])
            # apply_yes_no(, item, "hvo100" in location["fuel"])

            apply_yes_no(Extras.WIFI, item, "free-wifi" in location["other"])
            apply_yes_no(Extras.CAR_WASH, item, "machine-wash" in location["other"])
            apply_yes_no(Extras.SHOWERS, item, "shower" in location["other"])
            apply_yes_no(Extras.VACUUM_CLEANER, item, "vacuum-cleaner" in location["other"])
            apply_yes_no(Extras.TOILETS, item, "wc" in location["other"])

            apply_yes_no(Access.HGV, item, "truck" in location["tags"])
            apply_yes_no(Access.MOTOR_CAR, item, "passenger-car" in location["tags"])

            yield item
