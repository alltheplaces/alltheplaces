import json
import re
from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, Fuel, apply_category, apply_yes_no
from locations.dict_parser import DictParser


class WissolGESpider(Spider):
    name = "wissol_ge"
    item_attributes = {"brand": "ვისოლი", "brand_wikidata": "Q8027737"}
    start_urls = ["https://wissol.ge/ka/map"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        # Stations are a GeoJSON FeatureCollection embedded in `const allLocations = JSON.parse('...')`.
        if not (match := re.search(r"const allLocations = JSON\.parse\('(.+?)'\);", response.text, re.DOTALL)):
            self.logger.error("Wissol station data not found")
            return
        for feature in json.loads(json.loads('"' + match.group(1).replace("\\'", "'") + '"')):
            properties = feature["properties"]
            services = [(service.get("name") or {}).get("en") for service in properties.get("services") or []]
            # The map also lists non-fuel Wissol locations (Smart markets, Winto/Truck service centres, the
            # head office); keep only markers that actually dispense fuel.
            if not any(service in services for service in ("Standart", "Self Service", "CNG")):
                continue

            item = DictParser.parse(properties)  # id->ref, address->addr_full
            item["ref"] = str(properties["id"])
            item["geometry"] = feature["geometry"]
            if properties.get("working_hours") == "24/7":  # every Wissol station is open round the clock
                item["opening_hours"] = "24/7"

            # "CNG" (natural gas) and "Power Charger" (EV) are explicit fuel products; the "Standart"/
            # "Self Service" labels are only station formats, so no undifferentiated petrol/diesel tag.
            apply_yes_no(Fuel.CNG, item, "CNG" in services)
            apply_yes_no(Fuel.ELECTRIC, item, "Power Charger" in services)
            apply_category(Categories.FUEL_STATION, item)
            yield item
