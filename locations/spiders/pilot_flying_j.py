from typing import AsyncIterator, Iterable

from scrapy.http import JsonRequest, TextResponse

from locations.categories import Access, Categories, Fuel, apply_category, apply_yes_no
from locations.geo import country_iseadgg_centroids
from locations.hours import OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider

PILOT = {"brand": "Pilot", "brand_wikidata": "Q64128179"}
FLYING_J = {"brand": "Flying J", "brand_wikidata": "Q64130592"}
ONE9 = {"brand": "ONE9"}
TOWN_PUMP = {"brand": "Town Pump", "brand_wikidata": "Q7830004"}


class PilotFlyingJSpider(JSONBlobSpider):
    name = "pilot_flying_j"
    allowed_domains = ["pilotcompany.com"]
    locations_key = "locations"
    custom_settings = {"ROBOTSTXT_OBEY": False}

    async def start(self) -> AsyncIterator[JsonRequest]:
        for lat, lon in country_iseadgg_centroids(["US", "CA"], 458):
            yield JsonRequest(
                f"https://pilotcompany.com/api/locations/radiusSearch?latitude={lat}&longitude={lon}&radius=500"
            )

    def pre_process_data(self, feature: dict) -> None:
        lob = next(lob for lob in feature["linesOfBusiness"] if lob["isPrimaryLineOfBusiness"])
        feature["primary"] = lob
        feature.update({key: lob[key] for key in ("latitude", "longitude", "phone")})

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        lob = feature["primary"]
        if lob["isDealer"] or feature["status"] != "Open":
            return
        item["ref"] = feature["locationId"]
        item["name"] = lob["primaryBusinessDescription"]
        item["website"] = f"https://pilotcompany.com/locations/{feature['locationId']}"
        item["extras"]["fax"] = lob["fax"]

        item["opening_hours"] = OpeningHours()
        for rule in lob["hoursOfOperation"]:
            item["opening_hours"].add_range(rule["dayOfTheWeek"], rule["from"], rule["to"], time_format="%I:%M %p")

        apply_yes_no(Fuel.DIESEL, item, True)
        apply_yes_no(Fuel.HGV_DIESEL, item, True)
        apply_yes_no(Access.HGV, item, True)
        apply_category(Categories.FUEL_STATION, item)
        item.update(self.brand_info(lob))
        yield item

    def brand_info(self, lob: dict) -> dict:
        name = lob["primaryBusinessDescription"].upper()
        if lob["dieselBrandDescription"] == "Town Pump":
            return TOWN_PUMP
        elif name.startswith("PILOT"):
            return PILOT
        elif name.startswith("FLYING J"):
            return FLYING_J
        elif name.startswith("ONE9"):
            return ONE9
        return {}
