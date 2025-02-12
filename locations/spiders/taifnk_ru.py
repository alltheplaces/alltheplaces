from locations.categories import Categories, Fuel, apply_category, apply_yes_no
from locations.json_blob_spider import JSONBlobSpider


class TaifnkRUSpider(JSONBlobSpider):
    name = "taifnk_ru"
    item_attributes = {
        "brand": "Таиф-НК",
        "brand_wikidata": "Q112960401",
    }
    start_urls = ["https://taifazs.ru/tools/get-fuels.php"]
    FUEL_TYPES_MAPPING = {
        "АИ-92-К5 ЭКО": Fuel.OCTANE_92,
        "АИ-92-К5": Fuel.OCTANE_92,
        "АИ-95-К5": Fuel.OCTANE_95,
        "АИ-95-К5 ЭКО": Fuel.OCTANE_95,
        "АИ-98-К5": Fuel.OCTANE_98,
        "АИ-98-К5 ЭКО": Fuel.OCTANE_98,
        "дизель": Fuel.DIESEL,
        "газ": Fuel.LPG,
    }

    def post_process_item(self, item, response, location):
        item["ref"] = location["fuelShortcode"]
        item["branch"] = location["fuelName"]
        item["addr_full"] = location["fuelAdress"]
        item["phone"] = location["fuelPhone"]
        item["lat"] = location["fuelCoords"][0]
        item["lon"] = location["fuelCoords"][1]

        fuels = location.get("fuelType", []) or []  # Handle weird boolean fuel types value
        for fuel in fuels:
            if match := self.FUEL_TYPES_MAPPING.get(fuel):
                apply_yes_no(match, item, True)
            else:
                self.crawler.stats.inc_value(f"atp/{self.name}/fuel/fail/{fuel}")

        apply_category(Categories.FUEL_STATION, item)
        yield item
