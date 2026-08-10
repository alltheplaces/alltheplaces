import re

import chompjs
from scrapy import Spider

from locations.categories import Categories, Extras, Fuel, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.items import Feature
from locations.spiders.bp import BpSpider
from locations.spiders.exxon_mobil import ExxonMobilSpider
from locations.spiders.shell import ShellSpider
from locations.spiders.texaco_nl import TexacoNLSpider


class HaanNLSpider(Spider):
    name = "haan_nl"
    start_urls = ["https://tankstation.nl/tankstations/"]

    BRAND_MAPPING = {
        "argos": {"brand": "Argos", "brand_wikidata": "Q4750477"},
        "bp": BpSpider.brands["bp"],
        "de-haan": {"brand": "Haan", "brand_wikidata": "Q92553521"},
        "esso": ExxonMobilSpider.brands["Esso"],
        "esso-express": {"brand": "Esso Express", "brand_wikidata": "Q2350336"},
        "esso express": {"brand": "Esso Express", "brand_wikidata": "Q2350336"},
        "firezone": {"brand": "Firezone", "brand_wikidata": "Q14628080"},
        "maes": {"brand": "Maes"},
        "octa+": {"brand": "Octa+", "brand_wikidata": "Q2179978"},
        "shell": ShellSpider.item_attributes,
        "tamoil": {"brand": "Tamoil", "brand_wikidata": "Q706793"},
        "texaco": TexacoNLSpider.item_attributes,
        "vissers": {"brand": "Vissers", "brand_wikidata": "Q124253846"},
    }

    def parse(self, response):
        script_text = response.xpath('//script[contains(text(), "placesInitialData")]/text()').get()
        if not script_text:
            return

        match = re.search(r"placesInitialData\s*=\s*({.*?});", script_text, re.DOTALL)
        if not match:
            return

        data = chompjs.parse_js_object(match.group(1))
        locations = data.get("places", [])

        for location in locations:
            if not location.get("lat") or not location.get("long"):
                continue

            location["street_address"] = location.pop("street", None)
            location["website"] = location.pop("guid", None)

            item = DictParser.parse(location)
            item["branch"] = item.pop("name", None)

            brand_slug = location.get("brand")
            if brand_slug == "extern":
                self.handle_extern_brand(item, location)
            elif brand_slug:
                if brand_info := self.BRAND_MAPPING.get(brand_slug):
                    item.update(brand_info)
                else:
                    item.update(self.BRAND_MAPPING["de-haan"])
                    self.crawler.stats.inc_value("{}/unmapped_brand/{}".format(self.name, brand_slug))

            self.parse_fuel_types(location, item)
            self.parse_services(location, item)

            apply_category(Categories.FUEL_STATION, item)

            yield item

    def handle_extern_brand(self, item: Feature, location: dict):
        title = location.get("title", "")
        if not title:
            return

        # Extract brand name before "extern" (case-insensitive)
        if "extern" in title.lower():
            brand_part = re.split(r"extern", title, flags=re.IGNORECASE)[0].strip()
        else:
            brand_part = title.split()[0] if title.split() else ""

        # Look up brand in mapping
        brand_key = brand_part.lower()
        if brand_info := self.BRAND_MAPPING.get(brand_key):
            item.update(brand_info)
        else:
            # Set brand from extracted name if not in mapping
            item["brand"] = brand_part

        # Clean up branch name: remove "extern" and ID number
        branch = title
        # Remove "extern" followed by optional whitespace and digits (e.g., "extern 10003" or "extern18025")
        branch = re.sub(r"\s*extern\s*\d+", "", branch, flags=re.IGNORECASE)
        # Remove standalone "extern" word if still present (e.g., "Esso extern Groesbeek" -> "Esso Groesbeek")
        branch = re.sub(r"\s+extern\b", "", branch, flags=re.IGNORECASE)
        branch = branch.strip()

        item["branch"] = branch

    def parse_fuel_types(self, location: dict, item: Feature):
        gasoline_types = location.get("gasolineTypes", [])

        apply_yes_no(Fuel.OCTANE_95, item, "euro95" in gasoline_types)
        apply_yes_no(Fuel.DIESEL, item, "diesel" in gasoline_types)
        apply_yes_no(Fuel.LPG, item, "lpg" in gasoline_types)
        apply_yes_no(Fuel.CNG, item, "cng" in gasoline_types)
        apply_yes_no(Fuel.BIODIESEL, item, "hvo" in gasoline_types or "hvo100" in gasoline_types)

    def parse_services(self, location: dict, item: Feature):
        service_codes = list(map(lambda x: x.get("service"), location.get("services", [])))

        apply_yes_no(Extras.CAR_WASH, item, "carwash" in service_codes or "wasboxen" in service_codes)
        apply_yes_no("shop", item, "shop" in service_codes or "247_shop" in service_codes)
        apply_yes_no(Extras.TOILETS, item, "toilet" in service_codes)
        apply_yes_no(Extras.WIFI, item, "wifi" in service_codes)
