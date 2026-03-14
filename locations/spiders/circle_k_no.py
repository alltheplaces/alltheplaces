from scrapy.http import Response
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import Rule

from locations.categories import Categories, Fuel, apply_category, apply_yes_no
from locations.google_url import extract_google_position
from locations.items import Feature
from locations.spiders.circle_k_dk import CircleKDKSpider


class CircleKNOSpider(CircleKDKSpider):
    name = "circle_k_no"
    item_attributes = {"brand": "Circle K", "brand_wikidata": "Q3268010"}
    start_urls = ["https://www.circlek.no/stations"]
    rules = [Rule(LinkExtractor(allow="/station/circle"), callback="parse")]

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        if item["name"].startswith("CIRCLE K AUTOMAT "):
            item["branch"] = item.pop("name").removeprefix("CIRCLE K AUTOMAT ")
        elif item["name"].startswith("CIRCLE K TRUCK "):
            item["branch"] = item.pop("name").removeprefix("CIRCLE K TRUCK ")
            item["name"] = "Circle K Truck"
        elif item["name"].startswith("CIRCLE K LADER "):
            item["branch"] = item.pop("name").removeprefix("CIRCLE K LADER ")
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
        apply_yes_no(Fuel.OCTANE_95, item, "MilesPlus95" in fuels)
        apply_yes_no(Fuel.DIESEL, item, "MilesDiesel" in fuels)
        apply_yes_no(Fuel.DIESEL, item, "MilesPlusDiesel" in fuels)
        apply_yes_no(Fuel.UNTAXED_DIESEL, item, "Anleggsdiesel" in fuels)
        apply_yes_no(Fuel.BIODIESEL, item, "MilesBioHVO100" in fuels)

        yield item
