import re
from typing import Iterable

from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class MelbourneCityCouncilParkingSpacesAUSpider(JSONBlobSpider):
    name = "melbourne_city_council_parking_spaces_au"
    item_attributes = {"operator": "Melbourne City Council", "operator_wikidata": "Q56477763"}
    allowed_domains = ["data.melbourne.vic.gov.au"]
    start_urls = [
        "https://data.melbourne.vic.gov.au/api/explore/v2.1/catalog/datasets/on-street-parking-bay-sensors/exports/json?lang=en&timezone=Australia%2FSydney"
    ]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def start_requests(self) -> Iterable[JsonRequest]:
        yield JsonRequest(
            url="https://data.melbourne.vic.gov.au/api/explore/v2.1/catalog/datasets/sign-plates-located-in-each-parking-zone/exports/json?lang=en&timezone=Australia%2FSydney",
            callback=self.parse_parking_restrictions,
        )

    def parse_parking_restrictions(self, response: Response) -> Iterable[JsonRequest]:
        restrictions = {}
        for zone in response.json():
            if zone["parkingzone"] not in restrictions.keys():
                restrictions[zone["parkingzone"]] = {}
                restrictions[zone["parkingzone"]][
                    "type"
                ] = "normal"  # May be overridden with other values of https://wiki.openstreetmap.org/wiki/Key:parking_space
                restrictions[zone["parkingzone"]]["maxstay:conditional"] = {}
                restrictions[zone["parkingzone"]]["fee:conditional"] = {}
                restrictions[zone["parkingzone"]]["restriction:conditional"] = {}
            if zone["restriction_display"] == "HP":
                # Free parking up to 30 minutes duration
                if "30 minutes" not in restrictions[zone["parkingzone"]]["maxstay:conditional"].keys():
                    restrictions[zone["parkingzone"]]["maxstay:conditional"]["30 minutes"] = OpeningHours()
                restrictions[zone["parkingzone"]]["maxstay:conditional"]["30 minutes"].add_ranges_from_string(
                    "({}: {}-{})".format(
                        zone["restriction_days"], zone["time_restrictions_start"], zone["time_restrictions_finish"]
                    )
                )
                if "no" not in restrictions[zone["parkingzone"]]["fee:conditional"].keys():
                    restrictions[zone["parkingzone"]]["fee:conditional"]["no"] = OpeningHours()
                restrictions[zone["parkingzone"]]["fee:conditional"]["no"].add_ranges_from_string(
                    "({}: {}-{})".format(
                        zone["restriction_days"], zone["time_restrictions_start"], zone["time_restrictions_finish"]
                    )
                )
            elif zone["restriction_display"] == "PP":
                # Metered parking of unlimited duration
                if "unlimited" not in restrictions[zone["parkingzone"]]["maxstay:conditional"].keys():
                    restrictions[zone["parkingzone"]]["maxstay:conditional"]["unlimited"] = OpeningHours()
                restrictions[zone["parkingzone"]]["maxstay:conditional"]["unlimited"].add_ranges_from_string(
                    "({}: {}-{})".format(
                        zone["restriction_days"], zone["time_restrictions_start"], zone["time_restrictions_finish"]
                    )
                )
                if "yes" not in restrictions[zone["parkingzone"]]["fee:conditional"].keys():
                    restrictions[zone["parkingzone"]]["fee:conditional"]["yes"] = OpeningHours()
                restrictions[zone["parkingzone"]]["fee:conditional"]["yes"].add_ranges_from_string(
                    "({}: {}-{})".format(
                        zone["restriction_days"], zone["time_restrictions_start"], zone["time_restrictions_finish"]
                    )
                )
            elif zone["restriction_display"] == "QP" or zone["restriction_display"] == "FP15":
                # Free parking up to 15 minutes duration
                if "15 minutes" not in restrictions[zone["parkingzone"]]["maxstay:conditional"].keys():
                    restrictions[zone["parkingzone"]]["maxstay:conditional"]["15 minutes"] = OpeningHours()
                restrictions[zone["parkingzone"]]["maxstay:conditional"]["15 minutes"].add_ranges_from_string(
                    "({}: {}-{})".format(
                        zone["restriction_days"], zone["time_restrictions_start"], zone["time_restrictions_finish"]
                    )
                )
                if "no" not in restrictions[zone["parkingzone"]]["fee:conditional"].keys():
                    restrictions[zone["parkingzone"]]["fee:conditional"]["no"] = OpeningHours()
                restrictions[zone["parkingzone"]]["fee:conditional"]["no"].add_ranges_from_string(
                    "({}: {}-{})".format(
                        zone["restriction_days"], zone["time_restrictions_start"], zone["time_restrictions_finish"]
                    )
                )
            elif zone["restriction_display"] == "SP":
                # Free parking up to 5 minutes duration
                if "5 minutes" not in restrictions[zone["parkingzone"]]["maxstay:conditional"].keys():
                    restrictions[zone["parkingzone"]]["maxstay:conditional"]["5 minutes"] = OpeningHours()
                restrictions[zone["parkingzone"]]["maxstay:conditional"]["5 minutes"].add_ranges_from_string(
                    "({}: {}-{})".format(
                        zone["restriction_days"], zone["time_restrictions_start"], zone["time_restrictions_finish"]
                    )
                )
                if "no" not in restrictions[zone["parkingzone"]]["fee:conditional"].keys():
                    restrictions[zone["parkingzone"]]["fee:conditional"]["no"] = OpeningHours()
                restrictions[zone["parkingzone"]]["fee:conditional"]["no"].add_ranges_from_string(
                    "({}: {}-{})".format(
                        zone["restriction_days"], zone["time_restrictions_start"], zone["time_restrictions_finish"]
                    )
                )
            elif m := re.fullmatch(r"DP(\d+)P", zone["restriction_display"]):
                # Free parking for disability permit holders up to X hours duration
                maxstay = m.group(1)
                restrictions[zone["parkingzone"]]["type"] = "disabled"
                if f"{maxstay} hours" not in restrictions[zone["parkingzone"]]["maxstay:conditional"].keys():
                    restrictions[zone["parkingzone"]]["maxstay:conditional"][f"{maxstay} hours"] = OpeningHours()
                restrictions[zone["parkingzone"]]["maxstay:conditional"][f"{maxstay} hours"].add_ranges_from_string(
                    "({}: {}-{})".format(
                        zone["restriction_days"], zone["time_restrictions_start"], zone["time_restrictions_finish"]
                    )
                )
                if "no" not in restrictions[zone["parkingzone"]]["fee:conditional"].keys():
                    restrictions[zone["parkingzone"]]["fee:conditional"]["no"] = OpeningHours()
                restrictions[zone["parkingzone"]]["fee:conditional"]["no"].add_ranges_from_string(
                    "({}: {}-{})".format(
                        zone["restriction_days"], zone["time_restrictions_start"], zone["time_restrictions_finish"]
                    )
                )
            elif m := re.fullmatch(r"FP(\d+)P", zone["restriction_display"]):
                # Free parking up to X hours duration
                maxstay = m.group(1)
                if f"{maxstay} hours" not in restrictions[zone["parkingzone"]]["maxstay:conditional"].keys():
                    restrictions[zone["parkingzone"]]["maxstay:conditional"][f"{maxstay} hours"] = OpeningHours()
                restrictions[zone["parkingzone"]]["maxstay:conditional"][f"{maxstay} hours"].add_ranges_from_string(
                    "({}: {}-{})".format(
                        zone["restriction_days"], zone["time_restrictions_start"], zone["time_restrictions_finish"]
                    )
                )
                if "no" not in restrictions[zone["parkingzone"]]["fee:conditional"].keys():
                    restrictions[zone["parkingzone"]]["fee:conditional"]["no"] = OpeningHours()
                restrictions[zone["parkingzone"]]["fee:conditional"]["no"].add_ranges_from_string(
                    "({}: {}-{})".format(
                        zone["restriction_days"], zone["time_restrictions_start"], zone["time_restrictions_finish"]
                    )
                )
            elif m := re.fullmatch(r"LZ(\d+)", zone["restriction_display"]):
                # Loading zone up to X minutes duration
                maxstay = m.group(1)
                if f"{maxstay} minutes" not in restrictions[zone["parkingzone"]]["maxstay:conditional"].keys():
                    restrictions[zone["parkingzone"]]["maxstay:conditional"][f"{maxstay} minutes"] = OpeningHours()
                restrictions[zone["parkingzone"]]["maxstay:conditional"][f"{maxstay} minutes"].add_ranges_from_string(
                    "({}: {}-{})".format(
                        zone["restriction_days"], zone["time_restrictions_start"], zone["time_restrictions_finish"]
                    )
                )
                if "loading_only" not in restrictions[zone["parkingzone"]]["restriction:conditional"].keys():
                    restrictions[zone["parkingzone"]]["restriction:conditional"]["loading_only"] = OpeningHours()
                restrictions[zone["parkingzone"]]["restriction:conditional"]["loading_only"].add_ranges_from_string(
                    "({}: {}-{})".format(
                        zone["restriction_days"], zone["time_restrictions_start"], zone["time_restrictions_finish"]
                    )
                )
            elif m := re.fullmatch(r"(?:MP)?(\d+)P", zone["restriction_display"]):
                # Metered parking up to X hours duration
                maxstay = m.group(1)
                if f"{maxstay} hours" not in restrictions[zone["parkingzone"]]["maxstay:conditional"].keys():
                    restrictions[zone["parkingzone"]]["maxstay:conditional"][f"{maxstay} hours"] = OpeningHours()
                restrictions[zone["parkingzone"]]["maxstay:conditional"][f"{maxstay} hours"].add_ranges_from_string(
                    "({}: {}-{})".format(
                        zone["restriction_days"], zone["time_restrictions_start"], zone["time_restrictions_finish"]
                    )
                )
                if "yes" not in restrictions[zone["parkingzone"]]["fee:conditional"].keys():
                    restrictions[zone["parkingzone"]]["fee:conditional"]["yes"] = OpeningHours()
                restrictions[zone["parkingzone"]]["fee:conditional"]["yes"].add_ranges_from_string(
                    "({}: {}-{})".format(
                        zone["restriction_days"], zone["time_restrictions_start"], zone["time_restrictions_finish"]
                    )
                )
            else:
                raise ValueError("Unknown parking restriction: {}".format(zone["restriction_display"]))
        yield JsonRequest(url=self.start_urls[0], meta={"restrictions": restrictions}, callback=self.parse)

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = str(feature["kerbsideid"])
        apply_category(Categories.PARKING_SPACE, item)
        item["extras"]["access"] = "yes"
        all_restrictions = response.meta["restrictions"]
        if feature["zone_number"] in all_restrictions.keys():
            restrictions = all_restrictions[feature["zone_number"]]
            print(restrictions)
            item["extras"]["parking_space"] = restrictions["type"]
            for maxstay, hours in restrictions["maxstay:conditional"].items():
                if maxstay == "1 hours":
                    maxstay = "1 hour"
                hours_string = hours.as_opening_hours()
                if "maxstay:conditional" in item["extras"].keys():
                    item["extras"]["maxstay:conditional"] = (
                        item["extras"]["maxstay:conditional"] + f"; {maxstay} @ ({hours_string})"
                    )
                else:
                    item["extras"]["maxstay:conditional"] = f"{maxstay} @ ({hours_string})"
            for fee_status, hours in restrictions["fee:conditional"].items():
                hours_string = hours.as_opening_hours()
                if "fee:conditional" in item["extras"].keys():
                    item["extras"]["fee:conditional"] = (
                        item["extras"]["fee:conditional"] + f"; {fee_status} @ ({hours_string})"
                    )
                else:
                    item["extras"]["fee:conditional"] = f"{fee_status} @ ({hours_string})"
            for restriction, hours in restrictions["restriction:conditional"].items():
                hours_string = hours.as_opening_hours()
                if "restriction:conditional" in item["extras"].keys():
                    item["extras"]["restriction:conditional"] = (
                        item["extras"]["restriction:conditional"] + f"; {restriction} @ ({hours_string})"
                    )
                else:
                    item["extras"]["restriction:conditional"] = f"{restriction} @ ({hours_string})"
        yield item
