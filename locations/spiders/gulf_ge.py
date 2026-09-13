import json
import re
from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, Extras, Fuel, apply_category, apply_yes_no
from locations.dict_parser import DictParser


class GulfGESpider(Spider):
    name = "gulf_ge"
    item_attributes = {"brand": "გალფი", "brand_wikidata": "Q5617505"}
    start_urls = ["https://gulf.ge/ge/map"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        # Stations are embedded as a JS object keyed by id; the Google Maps script only renders them.
        if not (pins := re.search(r"var pins\s*=\s*(\{.*?\});", response.text, re.DOTALL)):
            self.logger.error("Gulf station data not found")
            return
        for pin in json.loads(pins.group(1)).values():
            if "GAS" not in (pin.get("poi_types") or []):
                continue  # a couple of non-fuel objects carry poi_types "OB"

            item = DictParser.parse(pin)  # id->ref, name, latitude/longitude->lat/lon
            item.pop("state", None)  # DictParser maps the "region" filter flag here; it is not an address region
            item["branch"] = item.pop("name")
            if address := re.search(r"\(([^()]+)\)\s*$", pin.get("description") or ""):  # "<name> (<address>)"
                item["addr_full"] = address.group(1).strip()

            fuels = pin.get("fuel_types") or []
            apply_yes_no(Fuel.DIESEL, item, any(fuel in fuels for fuel in ("ED", "GFED", "DE")))
            # Petrol grades (Euro Regular, G-Force Regular/Super/Premium) carry no octane numbers.
            apply_yes_no(Fuel.GASOLINE, item, any(fuel in fuels for fuel in ("ER", "GFER", "GFS", "GFP")))
            # In fuel_types, "CNG" is გაზი (gas); the "CNG" in poi_types is instead the "Gulf +" format.
            apply_yes_no(Fuel.CNG, item, "CNG" in fuels)
            apply_yes_no(Extras.FAST_FOOD, item, bool(pin.get("food_types")))
            apply_category(Categories.FUEL_STATION, item)
            yield item
