from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, MonitoringTypes, apply_yes_no
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class CaliforniaDepartmentOfTransportationRwisUSSpider(JSONBlobSpider):
    name = "california_department_of_transportation_rwis_us"
    item_attributes = {
        "operator": "California Department of Transportation",
        "operator_wikidata": "Q127743",
        "extras": Categories.MONITORING_STATION.value,
    }
    allowed_domains = ["cwwp2.dot.ca.gov"]
    start_urls = [
        "https://cwwp2.dot.ca.gov/data/d2/rwis/rwisStatusD02.json",
        "https://cwwp2.dot.ca.gov/data/d3/rwis/rwisStatusD03.json",
        "https://cwwp2.dot.ca.gov/data/d6/rwis/rwisStatusD06.json",
        "https://cwwp2.dot.ca.gov/data/d8/rwis/rwisStatusD08.json",
        "https://cwwp2.dot.ca.gov/data/d9/rwis/rwisStatusD09.json",
        "https://cwwp2.dot.ca.gov/data/d10/rwis/rwisStatusD10.json",
    ]

    def extract_json(self, response: Response) -> list[dict]:
        rwis_list = []
        for rwis in response.json()["data"]:
            if rwis["rwis"]["inService"] != "true":
                # RWIS disconnected/not in use and should be ignored.
                continue
            new_rwis = rwis["rwis"]["location"]
            new_rwis["id"] = rwis["rwis"]["location"]["district"] + "-" + rwis["rwis"]["index"]
            new_rwis["data"] = rwis["rwis"]["rwisData"]
            rwis_list.append(new_rwis)
        return rwis_list

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["state"] = "CA"
        apply_yes_no(
            MonitoringTypes.AIR_HUMIDITY,
            item,
            feature["data"]["humidityPrecipData"]["essRelativeHumidity"] != "Not Reported",
            False,
        )
        apply_yes_no(
            MonitoringTypes.AIR_PRESSURE,
            item,
            feature["data"]["stationData"]["essAtmosphericPressure"] != "Not Reported",
            False,
        )
        apply_yes_no(
            MonitoringTypes.AIR_TEMPERATURE,
            item,
            feature["data"]["temperatureData"]["essMaxTemp"] != "Not Reported"
            and feature["data"]["temperatureData"]["essMinTemp"] != "Not Reported",
            False,
        )
        apply_yes_no(
            MonitoringTypes.PRECIPITATION,
            item,
            feature["data"]["humidityPrecipData"]["essPrecipRate"] != "Not Reported",
            False,
        )
        apply_yes_no(
            MonitoringTypes.VISIBILITY,
            item,
            feature["data"]["visibilityData"]["essVisibilitySituation"] != "Not Reported",
            False,
        )
        apply_yes_no(
            MonitoringTypes.WIND_DIRECTION,
            item,
            feature["data"]["windData"]["essAvgWindDirection"] != "Not Reported",
            False,
        )
        apply_yes_no(
            MonitoringTypes.WIND_SPEED, item, feature["data"]["windData"]["essAvgWindSpeed"] != "Not Reported", False
        )
        yield item
