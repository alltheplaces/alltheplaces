from typing import AsyncIterator, Iterable

from scrapy.http import JsonRequest, Response

from locations.categories import Categories, MonitoringTypes, apply_category, apply_yes_no
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class EuroArgoEricFloatsSpider(JSONBlobSpider):
    name = "euro_argo_eric_floats"
    allowed_domains = ["fleetmonitoring.euro-argo.eu"]
    start_urls = ["https://fleetmonitoring.euro-argo.eu/floats/multi-lines-search/pages?page=1&size=10000"]
    custom_settings = {"ROBOTSTXT_OBEY": False, "DOWNLOAD_TIMEOUT": 30}
    # Skip reverse geocoding because most buoys are in international waters
    # or the reverse geocoder doesn't know where territorial borders exist.
    skip_auto_cc_geocoder = True
    skip_auto_cc_domain = True

    async def start(self) -> AsyncIterator[JsonRequest]:
        data = [
            {
                "nested": "false",
                "path": "string",
                "searchValueType": "Text",
                "values": ["A"],  # A = active floats only
                "field": "status",
            }
        ]
        yield JsonRequest(url=self.start_urls[0], data=data, method="POST")

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = feature["wmo"]
        item.pop("country", None)
        item["website"] = "https://fleetmonitoring.euro-argo.eu/float/" + item["ref"]

        # The "owner" is a messy data field that sometimes includes the
        # acronym for an organisation, or the name of an organisation, or a
        # person assigned at an organisation to be responsible for a subset of
        # floats. It is kept to give a rough idea of the operating country or
        # organisation of each float.
        if owner := feature.get("owner"):
            item["operator"] = owner

        # OSM doesn't offer a good tagging scheme for floats/drifters. The
        # closest tagging is for "ODAS" (Ocean Data Acquisition System) buoys.
        apply_category(Categories.MONITORING_STATION, item)
        item["extras"]["seamark:type"] = "buoy_special_purpose"
        item["extras"]["seamark:buoy_special_purpose"] = "odas"

        # Features are floats which are described at
        # https://en.wikipedia.org/wiki/Float_(oceanography)
        # Floats sink into the ocean and rise again to transmit data, then
        # sink back down again for another data collection cycle. The current
        # location of a float could be quite different from its last reported
        # position at time of last surfacing. Therefore the "check_date" key
        # is important to consider. This date may be greater than a week ago.
        if not feature["lastCycleBasicInfo"]["date"]:
            # Floats may have just been launched and haven't completed a cycle
            # yet. The data source contains information about where and when a
            # float was originally deployed that can be used instead.
            item["lat"] = feature["deployment"]["lat"]
            item["lon"] = feature["deployment"]["lon"]
            item["extras"]["check_date"] = feature["deployment"]["launchDate"].split("T", 1)[0]
        else:
            # The float has completed at least one cycle and has self-reported
            # a last known position.
            item["lat"] = feature["lastCycleBasicInfo"]["lat"]
            item["lon"] = feature["lastCycleBasicInfo"]["lon"]
            item["extras"]["check_date"] = feature["lastCycleBasicInfo"]["date"].split("T", 1)[0]

        item["extras"]["ref:wmo"] = item["ref"]
        if alt_ref := feature.get("serialInst"):
            item["extras"]["alt_ref"] = alt_ref
        if manufacturer := feature.get("maker"):
            item["extras"]["manufacturer"] = manufacturer
        if model := feature.get("model", feature["platform"]["type"]):
            item["extras"]["model"] = model

        # Extract monitoring types and attempt to map to existing OSM
        # "monitoring:*" keys as may already exist. Where such keys don't
        # exist, a string instead of MonitoringTypes Enum value is used. These
        # keys listed below as strings are made-up keys that probably don't
        # exist in OSM yet, and there doesn't appear to be any attempt in OSM
        # to consider such monitoring type (at least yet).
        #
        # To list and count all monitoring types in source data, use:
        # curl -s 'https://fleetmonitoring.euro-argo.eu/floats/multi-lines-search/pages?page=1&size=10000' -X POST -H 'Accept: application/json, text/plain, */*' -H 'Content-Type: application/json' --data-raw '[{"nested":false,"path":"string","searchValueType":"Text","values":["A"],"field":"status"}]' | jq '.[].variables[]' | sort | uniq -c
        apply_yes_no("monitoring:water_pressure", item, "SUBSURFACE PRESSURE" in feature["variables"])
        apply_yes_no(MonitoringTypes.SALINITY, item, "SUBSURFACE SALINITY" in feature["variables"])
        apply_yes_no(MonitoringTypes.WATER_TEMPERATURE, item, "SUBSURFACE TEMPERATURE" in feature["variables"])
        apply_yes_no(MonitoringTypes.DISSOLVED_OXYGEN, item, "OXYGEN" in feature["variables"])
        apply_yes_no(MonitoringTypes.WATER_PH, item, "PH" in feature["variables"])
        apply_yes_no(MonitoringTypes.WATER_NITRATE, item, "NITRATE" in feature["variables"])
        apply_yes_no(MonitoringTypes.SOLAR_RADIATION, item, "IRRADIANCE" in feature["variables"])
        apply_yes_no(MonitoringTypes.WATER_TURBIDITY, item, "BACKSCATTER" in feature["variables"])
        apply_yes_no("monitoring:chlorophyll", item, "CHLOROPHYLL" in feature["variables"])

        yield item
