import json
import re

from locations.categories import Categories, apply_category
from locations.json_blob_spider import JSONBlobSpider

# Address format is inconsistent (full state name or abbreviation, comma
# before the postcode or not), so only the parts that are reliably present
# are extracted here; state is left for StateCodeCleanUpPipeline to derive
# from the coordinates.
ADDRESS_RE = re.compile(
    r"^(?P<street>.+?),\s*(?P<city>[^,]+?),\s*[A-Za-z .]+?,?\s+(?P<postcode>[0-9]{4,5}(?:-[0-9]{4})?)\s*,\s*(?:United States|USA)\s*$"
)


class JoltUSSpider(JSONBlobSpider):
    name = "jolt_us"
    item_attributes = {"operator": "Jolt", "operator_wikidata": "Q109783503"}
    start_urls = ["https://joltcharge.com/us/find-a-charger/"]

    def extract_json(self, response):
        script = response.xpath("//script[contains(., 'var jolt = ')]/text()").get()
        if not script:
            self.logger.error("Could not find 'var jolt' script in page source")
            return []
        start = script.index("var jolt = ") + len("var jolt = ")
        data, _ = json.JSONDecoder().raw_decode(script[start:])
        return list(data["charging_points"].values())

    def post_process_item(self, item, response, feature):
        del item["name"]  # the source "name" is an internal charger code, not a place name
        item["branch"] = feature["description"]

        if match := ADDRESS_RE.match(feature["address"]):
            item["street_address"] = match.group("street")
            item["city"] = match.group("city")
            postcode, separator, suffix = match.group("postcode").partition("-")
            item["postcode"] = postcode.zfill(5) + (separator + suffix if separator else "")
            item["country"] = "US"
        else:
            item["addr_full"] = feature["address"]
            self.crawler.stats.inc_value(f"atp/{self.name}/address_not_parsed")

        apply_category(Categories.CHARGING_STATION, item)

        yield item
