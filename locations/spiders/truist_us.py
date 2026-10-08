import json
import re
from typing import Any, AsyncIterator

from scrapy import Request
from scrapy.http import Response

from locations.brand_utils import extract_located_in
from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.geo import point_locations, vincenty_distance
from locations.hours import OpeningHours
from locations.spiders.safeway import SafewaySpider
from locations.structured_data_spider import StructuredDataSpider
from locations.user_agents import BROWSER_DEFAULT


class TruistUSSpider(StructuredDataSpider):
    name = "truist_us"
    item_attributes = {
        "brand": "Truist",
        "brand_wikidata": "Q795486",
    }
    states = ["AL", "DC", "FL", "GA", "KY", "MD", "MS", "NC", "NJ", "OH", "PA", "SC", "TN", "TX", "VA", "WV"]
    search_radius = 25
    truncated_results = 90
    min_radius = 0.5
    wanted_types = ["FinancialService", "AutomatedTeller"]
    search_for_twitter = False
    search_for_phone = False
    drop_attributes = {"facebook"}
    custom_settings = {"USER_AGENT": BROWSER_DEFAULT}

    LOCATED_IN_MAPPINGS = [
        (["SAFEWAY"], SafewaySpider.item_attributes),
    ]

    async def start(self) -> AsyncIterator[Request]:
        for lat, lon in point_locations("us_centroids_25mile_radius_state.csv", self.states):
            yield self.search_request(lat, lon, self.search_radius)

    def search_request(self, lat: float, lon: float, radius: float) -> Request:
        return Request(
            url=f"https://www.truist.com/truist-api/branchlocator/locations.json?locationType=BOTH&lat={lat}&long={lon}&searchRadius={radius}",
            callback=self.parse_search,
            cb_kwargs={"lat": lat, "lon": lon, "radius": radius},
        )

    def parse_search(self, response: Response, lat: float, lon: float, radius: float, **kwargs: Any) -> Any:
        locations = response.json()["location"]
        for location in locations:
            yield Request(url="https://www.truist.com" + location["url"], callback=self.parse_sd)
        if len(locations) >= self.truncated_results and all(
            float(location["locationDistance"]) <= radius for location in locations
        ):
            sub_radius = round(radius * 0.71, 2)
            if sub_radius >= self.min_radius:
                for bearing in (45, 135, 225, 315):
                    sub_lat, sub_lon = vincenty_distance(lat, lon, sub_radius * 1.609344, bearing)
                    yield self.search_request(round(sub_lat, 5), round(sub_lon, 5), sub_radius)

    def post_process_item(self, item, response, ld_data, **kwargs):
        # Name is formatted something like:
        # "Truist Somewhere Branch in City, XY, 00000"
        # or
        # "Truist Somewhere ATM in City, XY, 00000"
        branch = item.pop("name").removeprefix("Truist ")
        i = branch.find(" Branch")
        if i == -1:
            i = branch.find(" ATM")
        if i != -1:
            branch = branch[:i]
        item["branch"] = branch

        location_info = json.loads(response.xpath("//@data-location-info").get())
        item["ref"] = location_info.get("locationKey")
        if location_info.get("locationType").upper() == "BRANCH":
            if atm_detail := location_info.get("atmDetail"):
                atm = item.deepcopy()
                atm["ref"] = atm_detail[0].get("atmId")
                atm["phone"] = None
                atm["opening_hours"] = "24/7"
                apply_category(Categories.ATM, atm)
                if branch:
                    atm["located_in"], atm["located_in_wikidata"] = extract_located_in(
                        branch, self.LOCATED_IN_MAPPINGS, self
                    )
                yield atm
            apply_category(Categories.BANK, item)
        elif location_info.get("locationType").upper() == "ATM":
            apply_category(Categories.ATM, item)
            item["phone"] = None
            if branch:
                item["located_in"], item["located_in_wikidata"] = extract_located_in(
                    branch, self.LOCATED_IN_MAPPINGS, self
                )

        if ld_data["openingHours"] == "24 Hours":
            item["opening_hours"] = "24/7"
        else:
            oh = OpeningHours()
            for line in ld_data["openingHours"].split(", "):
                line = re.sub(r"(\d)\D+$", r"\1", line)
                # Website implies PM of ending time, but OpeningHours assumes AM, so need to make explicit
                if line[-1].isdigit():
                    line += "PM"
                oh.add_ranges_from_string(line)
            item["opening_hours"] = oh

        item["extras"]["fax"] = location_info.get("fax")
        yield item

    def extract_amenity_features(self, item, response, ld_item):
        apply_yes_no(
            Extras.DRIVE_THROUGH,
            item,
            any(feature["name"] in ("Drive-up Window", "Drive Up") for feature in ld_item.get("amenityFeature", [])),
        )
        apply_yes_no(
            Extras.WHEELCHAIR,
            item,
            any(feature["name"] == "Handicapped Accessible" for feature in ld_item.get("amenityFeature", [])),
        )
