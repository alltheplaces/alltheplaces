from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, Fuel, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.spiders.seven_eleven_au import SEVEN_ELEVEN_SHARED_ATTRIBUTES

PREEM = {"brand": "Preem", "brand_wikidata": "Q598835"}
UNOX = {"brand": "Uno-X", "brand_wikidata": "Q3362746"}
YX = {"brand": "YX", "brand_wikidata": "Q4580519"}


class YxSpider(Spider):
    name = "yx"
    start_urls = ["https://www.preem.no/stations-store.json"]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json().get("data"):
            item = DictParser.parse(location)
            item["name"] = location["stationName"]
            item["ref"] = location["stationCode"]

            if "YX" in item["name"] and "7-Eleven" not in item["name"]:
                item.update(YX)
                item["branch"] = item.pop("name").removeprefix("YX ")
                apply_category(Categories.FUEL_STATION, item)
            elif "Uno-X" in item["name"] and "7-Eleven" not in item["name"]:
                item.update(UNOX)
                item["branch"] = item.pop("name").removeprefix("Uno-x ")
                apply_category(Categories.FUEL_STATION, item)
            elif "7-Eleven" in item["name"]:
                item.update(SEVEN_ELEVEN_SHARED_ATTRIBUTES)
                item["branch"] = item.pop("name").removeprefix("Yx ").removeprefix("7-eleven ").removeprefix("Uno-X ")
                apply_category(Categories.SHOP_CONVENIENCE, item)
            else:
                item.update(PREEM)
                item["name"] = None
                apply_category(Categories.FUEL_STATION, item)

            for fuel_type in location.get("fuelTypes") or []:
                apply_yes_no(Fuel.ADBLUE, item, "adblue" in fuel_type["name"].lower())
                apply_yes_no(Fuel.DIESEL, item, "diesel" in fuel_type["name"].lower())
                apply_yes_no(Fuel.OCTANE_95, item, "bensin95" in fuel_type["name"].lower())
                apply_yes_no(Fuel.OCTANE_98, item, "bensin98" in fuel_type["name"].lower())
                apply_yes_no(Fuel.BIODIESEL, item, "hvo100" in fuel_type["name"].lower())
            yield item
