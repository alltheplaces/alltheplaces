from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, Extras, Fuel, apply_category, apply_yes_no
from locations.google_url import extract_google_position
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class CircleKDKSpider(SitemapSpider, StructuredDataSpider):
    name = "circle_k_dk"
    item_attributes = {"brand": "Circle K", "brand_wikidata": "Q3268010"}
    sitemap_urls = ["https://www.circlek.dk/sitemaps/stations/sitemap.xml"]
    sitemap_rules = [(r"/station/(?!ingo-)[-\w]+", "parse_sd")]

    def pre_process_data(self, ld_data: dict, **kwargs):
        rules = ld_data.get("openingHours") or []
        for idx, rule in enumerate(rules):
            if len(rule) == 2:
                rules[idx] = "{} 00:00-24:00".format(rule)
        ld_data["openingHours"] = rules

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        category = Categories.FUEL_STATION
        if item["name"].startswith("CIRCLE K TRUCK ") or item["name"].startswith("TRUCKANLÆG "):
            item["branch"] = item.pop("name").removeprefix("CIRCLE K TRUCK ").removeprefix("TRUCKANLÆG ")
            item["name"] = "Circle K Truck"
        elif "TRUCK HOME" in item["name"].replace(",", ""):
            item["name"] = "Circle K Truck"
        elif item["name"].startswith("CIRCLE K MOTORVEJSCENTER "):
            item["branch"] = item.pop("name").removeprefix("CIRCLE K MOTORVEJSCENTER ")
            item["name"] = "Circle K Motorvejscenter"
        elif item["name"].startswith("CIRCLE K EV "):
            item["branch"] = item.pop("name").removeprefix("CIRCLE K EV ")
            item["name"] = "Circle K"
            category = Categories.CHARGING_STATION
        elif item["name"].startswith("CIRCLE K "):
            item["branch"] = item.pop("name").removeprefix("CIRCLE K ")

        extract_google_position(item, response)

        apply_category(category, item)

        fuels = [
            fuel.strip("/").rsplit("/", 1)[-1].removeprefix("Feature").removeprefix("Fuel")
            for fuel in response.xpath('//*[@class="field-fuel-list"][1]//img/@src').getall()
        ]

        apply_yes_no(Fuel.ADBLUE, item, "AdBlue" in fuels)
        apply_yes_no(Fuel.OCTANE_95, item, "Miles95" in fuels)
        apply_yes_no(Fuel.OCTANE_95, item, "MilesPlus95" in fuels)
        apply_yes_no(Fuel.DIESEL, item, "MilesDiesel" in fuels)
        apply_yes_no(Fuel.DIESEL, item, "MilesPlusDiesel" in fuels)
        apply_yes_no(Fuel.BIODIESEL, item, "HVO100" in fuels)
        apply_yes_no(Fuel.ELECTRIC, item, "EVCharger" in fuels and category != Categories.CHARGING_STATION)

        services = [
            service.split("?")[0].rsplit("/", 1)[-1].removeprefix("Feature")
            for service in response.xpath('//*[@itemprop="makesOffer"]//img/@src').getall()
        ]

        apply_yes_no(Extras.WIFI, item, "Wifi" in services)
        apply_yes_no(Extras.CAR_WASH, item, "CarWash" in services or "CarWashJetWash" in services)
        apply_yes_no(Extras.VACUUM_CLEANER, item, "VacuumCleaner" in services)
        apply_yes_no(Extras.SHOWERS, item, "Shower" in services)
        apply_yes_no(Extras.TOILETS, item, "ToiletsBoth" in services)

        yield item
