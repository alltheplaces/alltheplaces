from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class TasmanianGovernmentFreeWifiAUSpider(JSONBlobSpider):
    name = "tasmanian_government_free_wifi_au"
    item_attributes = {
        "operator": "Government of Tasmania",
        "operator_wikidata": "Q3112571",
        "state": "TAS",
        "nsi_id": "N/A",
    }
    allowed_domains = ["www.digital.tas.gov.au"]
    start_urls = ["https://www.digital.tas.gov.au/__data/assets/file/0041/379967/locations.json"]
    no_refs = True
    locations_key = "locations"
    custom_settings = {"ROBOTSTXT_OBEY": False}  # Invalid robots.txt cannot be parsed

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["street_address"] = item.pop("addr_full", None)
        if hours_string := feature.get("wifiHours"):
            if hours_string != "Available on request":
                hours_string = hours_string.replace("Seven days a week,", "Mon-Sun:").replace(
                    "24 hours per day", "12:00am - 11:59pm"
                )
                item["opening_hours"] = OpeningHours()
                item["opening_hours"].add_ranges_from_string(hours_string)
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
