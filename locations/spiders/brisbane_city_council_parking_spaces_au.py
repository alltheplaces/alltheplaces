import re
from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature
from locations.storefinders.arcgis_feature_server import ArcGISFeatureServerSpider


class BrisbaneCityCouncilParkingSpacesAUSpider(ArcGISFeatureServerSpider):
    name = "brisbane_city_council_parking_spaces_au"
    item_attributes = {"operator": "Brisbane City Council", "operator_wikidata": "Q56477660", "state": "QLD"}
    host = "services2.arcgis.com"
    context_path = "dEKgZETqwmDAh1rP/ArcGIS"
    service_id = "parking_meters"
    layer_id = "0"

    # Ignore function complexity for the timebeing as a cleaner way of
    # handling parking restrictions (a very complex tagging technique) is
    # probably best implemented with a new ParkingRestrictions class (or
    # similar) that currently doesn't exist. More use cases for
    # a ParkingRestrictions class need to be identified because such class can
    # be developed in a way that accomodates parking restrictions as
    # implemented in a variety of countries of the world.
    # flake8: noqa: C901
    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = feature["METER_NO"]
        item["name"] = feature["LOC_DESC"]
        apply_category(Categories.PARKING, item)
        item["extras"]["access"] = "yes"
        item["extras"]["capacity:motorcar"] = str(feature["VEH_BAYS"])
        item["extras"]["capacity:motorcycle"] = str(feature["MC_BAYS"])

        restriction_times = OpeningHours()
        if "MON-FRI" in feature["OPERATIONAL_TIME"] or "SAT,SUN" in feature["OPERATIONAL_TIME"]:
            time_ranges = feature["OPERATIONAL_TIME"].replace("SAT,SUN", "SAT-SUN").split(",")
            for time_range in time_ranges:
                days_applicable = None
                hours_range = None
                if "MON-FRI" in time_range:
                    days_applicable = "MON-FRI"
                elif "SAT-SUN" in time_range:
                    days_applicable = "SAT-SUN"
                else:
                    # Default range which duplicates Mon-Fri/Sat-Sun ranges.
                    # Example: 7AM-7PM (with no days specified).
                    # Can be ignored as this is less specific than the time
                    # ranges specified with days.
                    continue
                if m := re.search(r"(\d{1,2}(?:\:\d{2})?(?:AM|PM)-\d{1,2}(?:\:\d{2})?(?:AM|PM))", time_range):
                    hours_range = m.group(1)
                if not days_applicable or not hours_range:
                    self.logger.warning("Could not parse time range(s) from provided string: {}".format(time_range))
                    continue
                restriction_times.add_ranges_from_string(f"{days_applicable}: {hours_range}")
        else:
            restriction_times.add_ranges_from_string("{}: {}".format(feature["OPERATIONAL_DAY"], feature["OPERATIONAL_TIME"]))

        if feature["MAX_STAY_HRS"]:
            max_stay_hours = int(feature["MAX_STAY_HRS"].replace("4P-12P", "12"))
            if max_stay_hours == 1:
                item["extras"]["maxstay:conditional"] = "1 hour @ ({})".format(restriction_times.as_opening_hours())
            else:
                item["extras"]["maxstay:conditional"] = "{} hours @ ({})".format(max_stay_hours, restriction_times.as_opening_hours())

        item["extras"]["fee:conditional"] = "yes @ ({})".format(restriction_times.as_opening_hours())

        if feature["VEH_BAYS"] and int(feature["VEH_BAYS"]) > 0:
            vehicle_type = ""
            if feature["MC_BAYS"] and int(feature["MC_BAYS"]) > 0:
                vehicle_type = "motorcar:"
            if feature["TAR_RATE_WEEKDAY"] and feature["TAR_RATE_AH_WE"]:
                item["extras"][f"{vehicle_type}charge:conditional"] = "{} AUD/hour @ (Mo-Fr 07:00-19:00); {} AUD/hour @ (Mo-Fr 19:00-24:00; Sa-Su 07:00-19:00)".format(feature["TAR_RATE_WEEKDAY"], feature["TAR_RATE_AH_WE"])
            elif feature["TAR_RATE_WEEKDAY"] and not feature ["TAR_RATE_AH_WE"]:
                item["extras"][f"{vehicle_type}charge:conditional"] = "{} AUD/hour @ (Mo-Fr 07:00-19:00)".format(feature["TAR_RATE_WEEKDAY"])
            elif not feature["TAR_RATE_WEEKDAY"] and feature["TAR_RATE_AH_WE"]:
                item["extras"][f"{vehicle_type}charge:conditional"] = "{} AUD/hour @ (Mo-Fr 19:00-11:59; Sa-Su 07:00-19:00)".format(feature["TAR_RATE_AH_WE"])
        if feature["MC_BAYS"] and int(feature["MC_BAYS"]) > 0 and feature["MC_RATE"]:
            vehicle_type = ""
            if feature["VEH_BAYS"] and int(feature["VEH_BAYS"]) > 0:
                vehicle_type = "motorcycle:"
            item["extras"][f"{vehicle_type}charge:conditional"] = "{} AUD/hour @ ({})".format(feature["MC_RATE"], restriction_times.as_opening_hours())

        yield item
