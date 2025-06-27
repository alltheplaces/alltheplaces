from datetime import datetime, timedelta, UTC
from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.arcgis_feature_server import ArcGISFeatureServerSpider


class OceanopsGdpDriftersSpider(ArcGISFeatureServerSpider):
    """
    This spider captures active drifters within the Global Drifter Program
    that has Wikidata item Q9268751 and homepage of:
    https://www.aoml.noaa.gov/phod/gdp/index.php

    The OceanOPS website is backed by the UNESCO Intergovernmental
    Oceanographic Commission and the World Meteorological Organization and
    offers what appears to be a more up-to-date and easy-to-use interface for
    obtaining drifter data than what NOAA AOML offers on their website. NOAA
    AOML for example has drifter metadata published but it is weeks out of
    date and seemingly updated somewhat infrequently.
    """
    name = "oceanops_gdp_drifters"
    host = "www.ocean-ops.org"
    context_path = "arcgis"
    service_id = "DBCP/DBCPLocations"
    server_type = "MapServer"
    layer_id = "1"
    # Skip reverse geocoding because drifters are mostly in international
    # waters or the reverse geocoder doesn't know where territorial borders
    # exist.
    skip_auto_cc_geocoder = True
    skip_auto_cc_domain = True

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        if feature["ptf_family"] != "DB":
            # Not a drifting buoy part of the Global Drifter Array. Ignore
            # feature as other ATP spiders address it.
            return

        item["ref"] = feature["wmo"]
        item.pop("country", None)

        # OSM doesn't offer a good tagging scheme for drifters. The closest
        # tagging is for "ODAS" (Ocean Data Acquisition System) buoys.
        apply_category(Categories.MONITORING_STATION, item)
        item["extras"]["seamark:type"] = "buoy_special_purpose"
        item["extras"]["seamark:buoy_special_purpose"] = "odas"

        if location_report_unix_timestamp := feature.get("loc_date"):
            location_report_date = datetime.fromtimestamp(int(float(location_report_unix_timestamp) / 1000), UTC)
            if location_report_date < datetime.now(UTC) - timedelta(days=3):
                # Drifter may be out of service / removed if it hasn't
                # reported data and a position in the last 3 days. This 3 day
                # threshold roughly results in the same number of active
                # drifters as listed on the official map at:
                # https://www.aoml.noaa.gov/phod/gdp/interactive/drifter_array.html
                # There isn't much variance in drifters deemed active if this
                # threshold is changed to 2 days, 7 days or 14 days but 3 days
                # seems to be a reasonable compromise that fairly closely
                # matches the threshold used on the official map.
                return
            elif location_report_date > datetime.now(UTC):
                # Some drifters have location report and/or deployment dates
                # set in the future. Maybe these are planned deployments mixed
                # into the dataset alongside already-deployed drifters. Ignore
                # such drifters.
                return
            item["extras"]["check_date"] = location_report_date.strftime("%Y-%m-%d")
        else:
            # Ignore drifters that have no last report date. These are most
            # likely old drifters no longer in service, possibly because they
            # failed to deploy.
            # https://www.aoml.noaa.gov/phod/gdp/erddap/metrics/index.php says
            # that ~3.7% of drifters have failed on deployment since 1979.
            return

        if deployment_unix_timestamp := feature.get("depl_date"):
            deployment_date = datetime.fromtimestamp(int(float(deployment_unix_timestamp) / 1000), UTC)
            if deployment_date > datetime.now(UTC):
                # Some drifters have location report and/or deployment dates
                # set in the future. Maybe these are planned deployments mixed
                # into the dataset alongside already-deployed drifters. Ignore
                # such drifters.
                return
            item["extras"]["start_date"] = deployment_date.strftime("%Y-%m-%d")

        item["extras"]["ref:wmo"] = feature["wmo"]

        if model := feature.get("ptf_model"):
            item["extras"]["model"] = model

        yield item
