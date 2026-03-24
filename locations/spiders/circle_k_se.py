from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, Fuel, apply_category, apply_yes_no
from locations.google_url import extract_google_position
from locations.items import Feature
from locations.spiders.circle_k_dk import CircleKDKSpider


class CircleKSESpider(CircleKDKSpider):
    name = "circle_k_se"
    start_urls = ["https://www.circlek.se/stations"]

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs) -> Iterable[Feature]:
        if item["name"].startswith("CIRCLE K TRUCK "):
            item["branch"] = item.pop("name").removeprefix("CIRCLE K TRUCK ")
            item["name"] = "Circle K Truck"
        elif item["name"].startswith("CIRCLE K "):
            item["branch"] = item.pop("name").removeprefix("CIRCLE K ")

        extract_google_position(item, response)

        fuels = [
            fuel.split("FeatureFuel")[-1]
            for fuel in response.xpath('//img[contains(@src, "FeatureFuel")]/@src').getall()
        ]
        charging_station = response.xpath('//img[contains(@src, "FeatureEVCharger")]/@src').get()
        if not fuels and charging_station:
            apply_category(Categories.CHARGING_STATION, item)
        else:
            apply_category(Categories.FUEL_STATION, item)
            apply_yes_no(Fuel.ELECTRIC, item, bool(charging_station))

        apply_yes_no(Fuel.ADBLUE, item, "AdBlue" in fuels)
        apply_yes_no(Fuel.OCTANE_95, item, "Miles95" in fuels)
        apply_yes_no(Fuel.OCTANE_98, item, "Miles98" in fuels)
        apply_yes_no(Fuel.OCTANE_98, item, "MilesPlus98" in fuels)
        apply_yes_no(Fuel.E85, item, "E85" in fuels)
        apply_yes_no("fuel:ed95", item, "ED95" in fuels)
        apply_yes_no(Fuel.DIESEL, item, "MilesDiesel" in fuels)
        apply_yes_no(Fuel.DIESEL, item, "MilesPlusDiesel" in fuels)
        apply_yes_no(Fuel.CNG, item, "CNG" in fuels)
        apply_yes_no(Fuel.BIODIESEL, item, "B100" in fuels)
        apply_yes_no(Fuel.BIODIESEL, item, "HVO100" in fuels)

        yield item
