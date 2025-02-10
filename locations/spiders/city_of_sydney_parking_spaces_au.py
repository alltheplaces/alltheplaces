import re
from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature
from locations.storefinders.arcgis_feature_server import ArcGISFeatureServerSpider


class CityOfSydneyParkingSpacesAUSpider(ArcGISFeatureServerSpider):
    name = "city_of_sydney_parking_spaces_au"
    item_attributes = {"operator": "City of Sydney", "operator_wikidata": "Q56477532", "state": "NSW"}
    host = "utility.arcgis.com"
    context_path = "usrsvcs/servers/4f7beba11d28427282b97f024a695c14"
    service_id = "ParkingMeters"
    server_type = "MapServer"
    layer_id = "78"

    # Ignore function complexity for the timebeing as a cleaner way of
    # handling parking restrictions (a very complex tagging technique) is
    # probably best implemented with a new ParkingRestrictions class (or
    # similar) that currently doesn't exist. More use cases for
    # a ParkingRestrictions class need to be identified because such class can
    # be developed in a way that accomodates parking restrictions as
    # implemented in a variety of countries of the world.
    # flake8: noqa: C901
    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = feature["Meter_ID"]
        apply_category(Categories.PARKING, item)
        if capacity := feature.get("ApproxPaySpaces"):
            item["extras"]["capacity"] = int(capacity)

        hours_by_max_stay = {}
        hours_fee_applicable = OpeningHours()
        hours_by_charge = {}
        for restriction_string in map(str.strip, feature.get("Popup", "").split(";")):
            restriction_string = restriction_string.replace("1/4P", "0.25P").replace("1/2P", "0.5P").replace(" & PUBLIC HOLIDAYS", "")
            if not restriction_string:
                # Some blank conditional restriction strings exist and should
                # be ignored.
                continue
            if m := re.search(r"^(\d{1,2}(?:\.\d{1,2})?)P\s+(\d{1,2}(?:\:\d{2})?(?:AM|PM)\s*-\s*\d{1,2}(?:\:\d{2})?(?:AM|PM))\s+((?:MON|TUE|WED|THU|FRI|SAT|SUN)(?:-(?:MON|TUE|WED|THU|FRI|SAT|SUN))?),\s+\$(\d{1,2}(?:\.\d{2})?)\s+\/HR$", restriction_string):
                max_stay = m.group(1)
                time_range = m.group(2)
                day_range = m.group(3)
                charge = m.group(4)
                if max_stay not in hours_by_max_stay.keys():
                    hours_by_max_stay[max_stay] = OpeningHours()
                hours_by_max_stay[max_stay].add_ranges_from_string("{}: {}".format(day_range, time_range))
                hours_fee_applicable.add_ranges_from_string("{}: {}".format(day_range, time_range))
                if charge not in hours_by_charge.keys():
                    hours_by_charge[charge] = OpeningHours()
                hours_by_charge[charge].add_ranges_from_string("{}: {}".format(day_range, time_range))
            else:
                self.logger.warning("Unable to parse parking restrictions string: {}".format(restriction_string))

        for max_stay, hours in hours_by_max_stay.items():
            max_stay_string = f"{max_stay} hours".replace("1 hours", "1 hour").replace("0.25 hours", "15 minutes").replace("0.5 hours", "30 minutes")
            if "maxstay:conditional" in item["extras"].keys():
                item["extras"]["maxstay:conditional"] = item["extras"]["maxstay:conditional"] + "; {} @ ({})".format(max_stay_string, hours.as_opening_hours())
            else:
                item["extras"]["maxstay:conditional"] = "{} @ ({})".format(max_stay_string, hours.as_opening_hours())

        item["extras"]["fee:conditional"] = "yes @ ({})".format(hours_fee_applicable.as_opening_hours())

        for charge, hours in hours_by_charge.items():
            if "charge:conditional" in item["extras"].keys():
                item["extras"]["charge:conditional"] = item["extras"]["charge:conditional"] + "; {} AUD/hour @ ({})".format(charge, hours.as_opening_hours())
            else:
                item["extras"]["charge:conditional"] = "{} AUD/hour @ ({})".format(charge, hours.as_opening_hours())

        yield item
