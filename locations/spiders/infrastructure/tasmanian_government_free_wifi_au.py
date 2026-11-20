from io import BytesIO
from typing import Iterable

from openpyxl import load_workbook
from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature


class TasmanianGovernmentFreeWifiAUSpider(Spider):
    name = "tasmanian_government_free_wifi_au"
    item_attributes = {
        "operator": "Government of Tasmania",
        "operator_wikidata": "Q3112571",
        "state": "TAS",
        "nsi_id": "N/A",
    }
    allowed_domains = ["www.tas.gov.au"]
    start_urls = ["https://www.tas.gov.au/digital/wi-fi-program/wifi-location-data.xlsx"]
    no_refs = True

    def parse(self, response: Response) -> Iterable[Feature]:
        workbook = load_workbook(BytesIO(response.body), read_only=True)
        sheet = workbook.active
        rows = []
        for row in sheet.iter_rows(values_only=True):
            rows.append(row)
        headers = rows[0]
        features = []
        for row in rows[1:]:
            features.append({headers[i]: cell for i, cell in enumerate(row)})

        for feature in features:
            item = Feature()
            item["name"] = feature["name"]
            item["lat"] = feature["latitude"]
            item["lon"] = feature["longitude"]
            item["street_address"] = feature["address"]
            item["city"] = feature["suburb"]

            if feature.get("wifiHours"):
                hours_text_reformatted = (
                    feature["wifiHours"]
                    .replace("Available on request", "")
                    .replace("Seven days a week, 24 hours per day", "Mon-Sun: 12:00am - 11:59pm")
                    .replace("Seven days a week,", "Mon-Sun: ")
                )
                item["opening_hours"] = OpeningHours()
                item["opening_hours"].add_ranges_from_string(hours_text_reformatted)

            apply_category(Categories.ANTENNA, item)
            item["extras"]["internet_access"] = "wlan"
            item["extras"]["internet_access:fee"] = "no"
            item["extras"]["internet_access:operator"] = self.item_attributes["operator"]
            item["extras"]["internet_access:operator:wikidata"] = self.item_attributes["operator_wikidata"]
            if item.get("name") and item["name"].endswith(" Library"):
                item["extras"]["internet_access:ssid"] = "Libraries_Tasmania"
            else:
                item["extras"]["internet_access:ssid"] = "TasGov_Free"

            yield item
