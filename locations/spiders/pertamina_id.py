from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, Extras, Fuel, apply_category, apply_yes_no
from locations.hours import DAYS, OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider

FUEL_MAPPING = {
    "Pertalite": Fuel.OCTANE_90,
    "Pertamax": Fuel.OCTANE_92,
    "Pertamax Green": Fuel.OCTANE_95,
    "Pertamax Plus": Fuel.OCTANE_95,
    "Pertamax Turbo": Fuel.OCTANE_98,
    "Bio Solar": Fuel.BIODIESEL,
    "DexLite": Fuel.DIESEL,
    "Solar": Fuel.DIESEL,
    "Premium": Fuel.OCTANE_88,
    "Pertamina Dex": Fuel.DIESEL,
    "Dexlite": Fuel.DIESEL,
}

FACILITY_MAPPING = {
    "Musholla": None,
    "Toilet Umum": Extras.TOILETS,
    "Parkir Umum": None,
    "Produk LPG": Fuel.LPG,
    "ATM": None,
    "Mini Market": None,
    "Cafe": None,
    "Restaurant": None,
    "Bengkel": None,
    "Car Wash": None,
    "Penggunaan Voucher BBK": None,
    "Penggunaan Kartu Pas RFID": None,
    "Produk Pelumas": Fuel.ENGINE_OIL,
}


class PertaminaIDSpider(JSONBlobSpider):
    name = "pertamina_id"
    item_attributes = {
        "brand": "Pertamina",
        "brand_wikidata": "Q1641044",
    }
    start_urls = ["https://api-stagingweb.pertaminaretail.com/location?page=1&limit=99999999"]
    locations_key = ["data"]

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        if fuel_str := feature.get("fuel"):
            fuel_types = [f.strip() for f in fuel_str.split(",")]
            for fuel_type in fuel_types:
                if mapped_fuel := FUEL_MAPPING.get(fuel_type):
                    apply_yes_no(mapped_fuel, item, True)
                else:
                    self.crawler.stats.inc_value(f"atp/pertamina_id/unknown_fuel/{fuel_type}")

        if facility_str := feature.get("facility"):
            facilities = [f.strip() for f in facility_str.split(",")]
            for facility in facilities:
                if mapped_facility := FACILITY_MAPPING.get(facility):
                    apply_yes_no(mapped_facility, item, True)
                else:
                    self.crawler.stats.inc_value(f"atp/pertamina_id/unknown_facility/{facility}")

        if hours_str := feature.get("operational_hour"):
            try:
                oh = OpeningHours()
                if "24 Jam" in hours_str:
                    oh.add_days_range(DAYS, "00:00", "24:00")
                elif "16 Jam" in hours_str and "06.00-22.00" in hours_str:
                    oh.add_days_range(DAYS, "06:00", "22:00")
                elif "-" in hours_str:
                    self.crawler.stats.inc_value(f"atp/{self.name}/unknown_hours_format")
                item["opening_hours"] = oh
            except Exception as e:
                self.logger.warning(f"Failed to parse hours: {hours_str}, {e}")

        apply_category(Categories.FUEL_STATION, item)
        yield item
