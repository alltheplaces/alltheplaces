import json
import re
from typing import Any

from scrapy.http import Response
from scrapy.spiders import Spider

from locations.categories import Categories, Extras, Fuel, apply_category, apply_yes_no
from locations.dict_parser import DictParser

ATTRIBUTES_MAP = {
    "Bulk DEF": None,
    "Certified Truck Scales": None,
    "Check Cashing": None,
    "Compressed Air": Extras.COMPRESSED_AIR,
    "Diesel": Fuel.DIESEL,
    "Drive Thru": Extras.DRIVE_THROUGH,
    "E85 Gas": Fuel.E85,
    "EV Charging": Fuel.ELECTRIC,
    "Ethanol Free": Fuel.ETHANOL_FREE,
    "Free WiFi": Extras.WIFI,
    "Fried Chicken": "food",
    "Gaming Machines": None,
    "High Flow Diesel Lanes": "hgv",
    "Mid-grade 89": Fuel.OCTANE_89,
    "Online Ordering": None,
    "Pizza": "food",
    "Premium 93": Fuel.OCTANE_93,
    "Regular 87": Fuel.OCTANE_87,
    "Reserved Truck Parking": None,
    "Seating Area": None,
    "Self Checkout": Extras.SELF_CHECKOUT,
    "Swirl World": None,
    "Travel Center": None,
    "Truck Merchandise": None,
    "Truck Parking": None,
}


class RaceTracUSSpider(Spider):
    name = "race_trac_us"
    item_attributes = {"brand": "RaceTrac", "brand_wikidata": "Q735942"}
    allowed_domains = ["www.racetrac.com"]
    start_urls = ["https://www.racetrac.com/locations/"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        if raw_data := re.search(
            r"storedata\s*=\s*(\[.*\]);\s*var", response.xpath('//*[contains(text(),"storedata")]/text()').get()
        ):
            for location in json.loads(raw_data.group(1)):
                item = DictParser.parse(location)
                item["street_address"] = location.get("StoreAddress1")
                if item.get("website"):
                    item["website"] = response.urljoin(item["website"])
                apply_category(Categories.FUEL_STATION, item)
                if amenities := location.get("Amenities"):
                    for amenity in amenities:
                        if attribute := ATTRIBUTES_MAP.get(amenity["DisplayName"]):
                            apply_yes_no(attribute, item, True)
                        else:
                            self.crawler.stats.inc_value(
                                "atp/racetrac_us/unmapped_attribute/{}".format(amenity["DisplayName"])
                            )
                yield item
