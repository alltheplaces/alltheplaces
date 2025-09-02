from typing import Iterable
from urllib.parse import quote

from scrapy import Selector
from scrapy.http import Response

from locations.categories import Categories, Fuel, apply_category, apply_yes_no
from locations.hours import CLOSED_EN, DAYS_EN, DELIMITERS_EN, OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.pipelines.address_clean_up import merge_address_lines
from locations.spiders.costco_ca_gb_us import COSTCO_SHARED_ATTRIBUTES


class CostcoAUSpider(JSONBlobSpider):
    name = "costco_au"
    item_attributes = COSTCO_SHARED_ATTRIBUTES
    allowed_domains = ["www.costco.com.au"]
    start_urls = ["https://www.costco.com.au/store-finder/search?q="]
    locations_key = "data"
    day_labels = DAYS_EN
    delimiters = DELIMITERS_EN
    closed_labels = CLOSED_EN

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = feature["warehouseCode"]
        item["branch"] = feature["displayName"]
        item.pop("name", None)
        item["street_address"] = merge_address_lines([feature.get("line1"), feature.get("line2")])
        item["website"] = self.start_urls[0].replace("search?q=", quote(item["branch"]))

        warehouse = item.deepcopy()
        if feature.get("openings"):
            warehouse["opening_hours"] = OpeningHours()
            hours_text = ""
            for day_name, day_hours in feature["openings"].items():
                hours_range = day_hours["individual"]
                hours_text = f"{hours_text} {day_name}: {hours_range}"
            warehouse["opening_hours"] = self.parse_hours_string(hours_text)
        apply_category(Categories.SHOP_WHOLESALE, warehouse)
        yield warehouse

        if not feature.get("availableServices"):
            return

        for service in feature["availableServices"]:
            if service["code"] != "GAS_STATION":
                continue
            fuel_station = item.deepcopy()
            fuel_station["ref"] = fuel_station["ref"] + "_FUEL"
            hours_text = " ".join(Selector(text=service["openingHours"]).xpath("//text()").getall())
            fuel_station["opening_hours"] = self.parse_hours_string(hours_text)
            if "gasTypes" in service.keys():
                fuel_types = [fuel["name"] for fuel in service["gasTypes"]]
                apply_yes_no(Fuel.OCTANE_87, fuel_station, "Regular" in fuel_types)
                apply_yes_no(Fuel.OCTANE_89, fuel_station, "レギュラー" in fuel_types)
                apply_yes_no(Fuel.OCTANE_91, fuel_station, "Unleaded 91" in fuel_types)
                apply_yes_no(Fuel.OCTANE_93, fuel_station, "Premium" in fuel_types)
                apply_yes_no(
                    Fuel.OCTANE_95,
                    fuel_station,
                    "Premium 95" in fuel_types or "Blyfri" in fuel_types or "95無鉛" in fuel_types,
                )
                apply_yes_no(Fuel.OCTANE_96, fuel_station, "ハイオク" in fuel_types)
                apply_yes_no(Fuel.OCTANE_98, fuel_station, "Premium 98" in fuel_types or "98無鉛" in fuel_types)
                apply_yes_no(
                    Fuel.DIESEL,
                    fuel_station,
                    "Diesel" in fuel_types
                    or "Premium Diesel" in fuel_types
                    or "柴油" in fuel_types
                    or "ディーゼル" in fuel_types,
                )
                apply_yes_no(Fuel.BIODIESEL, fuel_station, "HVO 100" in fuel_types)
                apply_yes_no(Fuel.KEROSENE, fuel_station, "灯油" in fuel_types)
            apply_category(Categories.FUEL_STATION, fuel_station)
            yield fuel_station
            break

    def parse_hours_string(self, hours_string: str) -> OpeningHours:
        oh = OpeningHours()
        oh.add_ranges_from_string(
            hours_string, days=self.day_labels, delimiters=self.delimiters, closed=self.closed_labels
        )
        return oh
