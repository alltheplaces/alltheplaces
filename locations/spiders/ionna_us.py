import json
import re

import scrapy

from locations.categories import Categories, apply_category
from locations.items import Feature


def extract_text_between(text: str, from_string: str, to_string: str):
    """
    Extracts text between two strings in a given text.
    :param text: The text to search in.
    :param from_string: The starting string.
    :param to_string: The ending string.
    :return: The substring between the two strings, not including the strings themselves. Returns None if either string is not found in the text.
    """
    start_index = text.find(from_string)
    if start_index == -1:
        return None
    start_index += len(from_string)

    end_index = text.find(to_string, start_index)
    if end_index == -1:
        return None

    return text[start_index:end_index].strip()


class IonnaUSSpider(scrapy.Spider):
    name = "ionna_us"
    item_attributes = {"brand": "IONNA", "brand_wikidata": "Q124528707"}
    start_urls = ["https://www.ionna.com/rechargeries/find-a-rechargery/"]

    def parse(self, response):
        locations = extract_text_between(response.text, "var locations = ", "for(var key in locations) {")
        # There is a trailing semicolon at the end of the string, so we need to remove it.
        locations = locations.rstrip(";")

        json_data = json.loads(locations)

        for location_id, location in json_data.items():
            # Skip locations that are not yet open. They indicate this with "Coming Soon" or
            # "Opening Soon" in the note field.
            if "Coming Soon" in location["note"] or "Opening Soon" in location["note"]:
                continue

            item = Feature(
                {
                    "ref": location_id,
                    "street_address": location["street"],
                    "city": location["city"],
                    "state": location["state"],
                    "postcode": location["postcode"],
                    "country": location["country"],
                    "image": location["image"],
                    "website": location["link"],
                    "lat": location["lat"],
                    "lon": location["lon"],
                }
            )

            item["extras"] = {
                "access": "public",
                "fee": "yes",
                "parking:fee": "no",
            }

            # Extract the connector types from the "specs" field. It's a string with some HTML formatting like
            # "<div class="find_map_info_specs"><strong>Connectors</strong>4 NACS | 6 CCS</div>"
            specs = extract_text_between(location["specs"], "<strong>Connectors</strong>", "</div>")
            if specs:
                nacs_count = 0
                ccs_count = 0
                for part in specs.split(" | "):
                    part = part.strip()
                    if m := re.match(r"(\d+)\s*NACS", part):
                        nacs_count = int(m.group(1))
                    elif m := re.match(r"(\d+)\s*CCS", part):
                        ccs_count = int(m.group(1))

                item["extras"]["socket:type1_combo"] = str(ccs_count)
                item["extras"]["socket:nacs"] = str(nacs_count)
                item["extras"]["capacity"] = str(ccs_count + nacs_count)
            apply_category(Categories.CHARGING_STATION, item)
            yield item
