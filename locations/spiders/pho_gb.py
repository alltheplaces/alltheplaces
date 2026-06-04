import json
from typing import Iterable

from scrapy.http import TextResponse

from locations.categories import Extras, apply_yes_no
from locations.hours import OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class PhoGBSpider(JSONBlobSpider):
    name = "pho_gb"
    item_attributes = {
        "brand": "Pho",
        "brand_wikidata": "Q108443630",
    }
    start_urls = ["https://www.phocafe.co.uk/all-locations/"]

    def extract_json(self, response: TextResponse) -> dict | list[dict]:
        return json.loads(
            response.xpath('//script[contains(text(), "locationsData")]/text()').re_first(
                r"locationsData[=\s]+(\[.+\])\s*;"
            )
        )

    def pre_process_data(self, feature: dict) -> None:
        feature.update(feature.pop("acf"))
        feature.update(feature.pop("map_location"))

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        item.pop("name")
        item["branch"] = feature["title"]["rendered"]
        if item.get("housenumber"):
            item["housenumber"] = str(item["housenumber"])
        item["addr_full"] = feature["nice_address"]
        item["website"] = feature["location_hp"]["url"].replace(
            "https://content.phocafe.co.uk/", "https://www.phocafe.co.uk/"
        )

        facilities_info = ""
        opening_times = feature["opening_times"]
        if "Please note" in opening_times:  # Split opening times from additional facility notes
            opening_times, facilities_info = feature["opening_times"].split("Please note", 1)

        facilities_info = facilities_info.replace("wheel chair", "wheelchair")
        apply_yes_no(
            Extras.WHEELCHAIR, item, "wheelchair access" in facilities_info or "step free access" in facilities_info
        )
        apply_yes_no(Extras.TOILETS_WHEELCHAIR, item, "disabled toilet" in facilities_info)

        item["opening_hours"] = self.parse_opening_hours(opening_times)
        yield item

    def parse_opening_hours(self, hours: str) -> OpeningHours:
        opening_hours = OpeningHours()
        opening_hours.add_ranges_from_string(hours)
        return opening_hours
