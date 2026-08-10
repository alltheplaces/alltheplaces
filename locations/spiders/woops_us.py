from scrapy.http import Response

from locations.hours import OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class WoopsUSSpider(JSONBlobSpider):
    name = "woops_us"
    item_attributes = {
        "brand_wikidata": "Q110474786",
        "brand": "Woops!",
    }
    allowed_domains = ["mobi2go.com"]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    start_urls = [
        "https://www.mobi2go.com/api/1/headoffice/9492/locations?fields=address,opening_hours,status&include_hidden=true"
    ]

    def pre_process_data(self, feature: dict):
        feature.update(feature.pop("address", {}))

    def post_process_item(self, item: Feature, response: Response, feature: dict):
        if feature.get("status") == "hidden":
            return None

        item["ref"] = feature["id"]
        item["branch"] = feature.get("name", "").replace("Woops!", "").strip()
        street_address = f"{feature.get('street_number', '')} {feature.get('street_name', '')}".strip()

        # Handle Minnesota's "Mobile" and Jenna's "PLACEHOLDER" addresses
        if "Mobile" in street_address or "PLACEHOLDER" in street_address:
            item["street_address"] = None
            item["city"] = feature.get("suburb")
        else:
            item["street_address"] = street_address

        item.pop("street", None)
        item.pop("housenumber", None)

        item["opening_hours"] = self.parse_hours(feature.get("opening_hours", {}))

        yield item

    def parse_hours(self, oh_dict: dict) -> OpeningHours:
        oh = OpeningHours()
        rules = oh_dict.get("pickup", {})

        if not any(isinstance(v, list) and v for v in rules.values()):
            rules = oh_dict.get("delivery", {})

        rules.pop("is_experimental_format", None)
        for day, times in rules.items():
            if isinstance(times, list):
                for time_range in times:
                    open_time, close_time = time_range.split("-")
                    oh.add_range(day, open_time.strip(), close_time.strip())
        return oh
