from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, Extras, Fuel, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.pipelines.address_clean_up import merge_address_lines


class NouriaUSSpider(Spider):
    name = "nouria_us"
    start_urls = ["https://nouria.com/wp-json/nouria/v1/locations"]
    item_attributes = {"brand": "Nouria", "brand_wikidata": "Q120637476"}

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json():
            location = location | location["address"]
            item = DictParser.parse(location)
            item["ref"] = item.pop("name").rsplit(" - ", 1)[1]
            item["website"] = location["link"]
            item["street_address"] = merge_address_lines(
                [location["address"]["address_line_1"], location["address"]["address_line_2"]]
            )

            # every location is a convenience store but not every location has a Nouria branded gas station
            if "nouria-fuel" in location["filters"]:
                fuel = item.deepcopy()
                fuel["ref"] = "{}_fuel".format(fuel["ref"])
                apply_category(Categories.FUEL_STATION, fuel)
                apply_yes_no(Fuel.DIESEL, fuel, "diesel" in location["filters"])
                apply_yes_no(Fuel.ELECTRIC, fuel, "ev-charging" in location["filters"])
                apply_yes_no(Extras.CAR_WASH, fuel, "golden-nozzle-car-wash" in location["filters"])
                yield fuel

            apply_category(Categories.SHOP_CONVENIENCE, item)
            apply_yes_no("sells:alcohol", item, "beer-wine" in location["filters"])

            yield item
