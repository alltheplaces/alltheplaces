import copy
import re
from typing import Iterable

from scrapy.http import Response

from locations.categories import Access, Categories, Drink, Extras, Fuel, PaymentMethods, apply_category, apply_yes_no
from locations.hours import OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider

BRANDS = {
    "Chevron": (
        {"brand": "Chevron", "brand_wikidata": "Q319642"},
        "https://www.chevronwithtechron.com/en_us/home/gas-station-near-me.html?/station/",
    ),
    "Texaco": (
        {"brand": "Texaco", "brand_wikidata": "Q775060"},
        "https://www.texaco.com/en_us/home/find-a-station.html?/station/",
    ),
}
BOTH_SERVICES_MAPPING = {
    # 'emgood'
    "restroom": Extras.TOILETS,
    "giftcard": PaymentMethods.GIFT_CARD,
    "mobilepmt": PaymentMethods.CONTACTLESS,
    "amznlocker": "post_office:parcel_pickup",
    "deliver": Extras.DELIVERY,
    "selfckout": Extras.SELF_CHECKOUT,
    "payinside": "payment:qr_code",
}
STATION_SERVICES_MAPPING = {
    "carwash": Extras.CAR_WASH,
    "servicebay": Extras.CAR_REPAIR,
    "truckstop": Access.HGV,
    "diesel": Fuel.DIESEL,
    "charge": Fuel.ELECTRIC,
    "fullsvcarwash": Extras.CAR_WASH,
    "cvxreward": "fuel:discount:chevron",
    "hydrogen": "fuel:H2",
    "e85": Fuel.E85,
    "cngas": Fuel.CNG,
    "propane": Fuel.PROPANE,
    "r99": Fuel.BIODIESEL,
    # 'loyalty'  # Grocery gas rewards
    # 'coco'  # COCO Sites
} | BOTH_SERVICES_MAPPING
STORE_SERVICES_MAPPING = {
    "beer": Drink.BEER,
    "coffee": Drink.COFFEE,
    "extras": "food",
    "icee": "drink:slushy",
} | BOTH_SERVICES_MAPPING


def slugify(s):
    return re.sub(r"\W+", "-", s)


class ChevronUSSpider(JSONBlobSpider):
    name = "chevron_us"
    start_urls = [
        "https://apis.chevron.com/api/StationFinder/alongtheway?clientid=A67B7471&geoLoc=((90%2C-180)%2C(-90%2C-180))&oLat=1&oLng=1"
    ]
    locations_key = "stations"

    def post_process_item(self, base_item: Feature, response: Response, location: dict) -> Iterable[Feature]:
        del base_item["name"]
        base_item["street_address"] = base_item.pop("addr_full")

        if location["hours"] == "24/7":
            base_item["opening_hours"] = "24/7"
        elif location["hours"]:
            oh = OpeningHours()
            oh.add_ranges_from_string(location["hours"])
            base_item["opening_hours"] = oh

        station = copy.deepcopy(base_item)

        if location["brand"] in BRANDS:
            tags, website_prefix = BRANDS[location["brand"]]
            station.update(tags)
        else:
            self.logger.warning(f"Unknown brand {location['brand']!r}")
            _, website_prefix = BRANDS["Chevron"]

        station["website"] = (
            f"{website_prefix}{slugify(location['address'])}-{slugify(location['city'])}-{location['state']}-{location['zip']}-id{location['id']}"
        )

        for service, tag in STATION_SERVICES_MAPPING.items():
            apply_yes_no(tag, station, location.get(service) == "1")

        apply_category(Categories.FUEL_STATION, station)

        yield station

        if location.get("extramile") == "1" or location.get("cstore") == "1":
            store = copy.deepcopy(base_item)
            store["ref"] += "-store"

            if location.get("extramile") == "1":
                store["brand"] = "ExtraMile"
                store["brand_wikidata"] = "Q64224605"
                store["website"] = (
                    f"https://www.chevronextramile.com/station-finder/{slugify(location['address'])}-{slugify(location['city'])}-{location['state']}-{location['zip']}-id{location['id']}/"
                )
            else:
                store["brand"] = station["brand"]
                store["brand_wikidata"] = station["brand_wikidata"]
                store["website"] = station["website"]

            for service, tag in STORE_SERVICES_MAPPING.items():
                apply_yes_no(tag, store, location.get(service) == "1")

            apply_category(Categories.SHOP_CONVENIENCE, store)

            yield store
