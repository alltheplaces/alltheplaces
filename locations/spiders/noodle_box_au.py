import re
from typing import Any, Iterable

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines

POSTCODE = re.compile(r"\b(\d{4})\b")
STATE = re.compile(r"\b(NSW|VIC|QLD|WA|SA|TAS|ACT|NT|Victoria)\b", re.IGNORECASE)


class NoodleBoxAUSpider(Spider):
    """
    Concept Eight brands share a website platform which serves all locations as JSON at /data/locations.
    Other Concept Eight brands can subclass this spider, overriding name, item_attributes, start_urls and cuisine.
    """

    name = "noodle_box_au"
    item_attributes = {"brand": "Noodle Box", "brand_wikidata": "Q7049671"}
    start_urls = ["https://www.noodlebox.com.au/data/locations"]
    cuisine = "noodle"

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Feature]:
        for location in response.json()["data"]:
            item = Feature()
            item["ref"] = item["branch"] = location["name"]
            item["lat"], item["lon"] = location["latlng"].split(",")
            item["addr_full"] = merge_address_lines(location.get("address") or [])
            item["city"] = location.get("suburb")
            item["state"] = location.get("state")
            item["postcode"] = location.get("postcode")
            if not item["city"] or not item["state"] or not item["postcode"]:
                self.extract_address_parts(item, location.get("address") or [])
            item["phone"] = (location.get("contact") or {}).get("phone")

            apply_category(Categories.FAST_FOOD, item)
            item["extras"]["cuisine"] = self.cuisine
            item["extras"]["takeaway"] = "yes"
            yield item

    @staticmethod
    def extract_address_parts(item: Feature, address_lines: list[str]) -> None:
        # Some brands only provide address lines, ending with e.g. "Altona North VIC 3025"
        last_line = next((line for line in reversed(address_lines) if line and line.strip()), "")
        if not item["postcode"]:
            if postcodes := POSTCODE.findall(last_line):
                item["postcode"] = postcodes[-1]
        if m := STATE.search(last_line):
            if not item["state"]:
                item["state"] = m.group(1).upper().replace("VICTORIA", "VIC")
            if not item["city"]:
                # City is the last comma separated part before the state, e.g. "Shop 3, 440 Brisbane Road, Arundel QLD"
                before_state = POSTCODE.sub("", last_line[: m.start()]).split(",")
                city = next((part.strip() for part in reversed(before_state) if part.strip()), "")
                if city and not re.search(r"\d", city):
                    item["city"] = city
