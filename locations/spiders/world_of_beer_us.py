import json
import re
from typing import Any, Iterable

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature

# The locations page carries every tavern in the site_info JavaScript object,
# as a JSON string holding the address, coordinates, phone and page link.
#
# Taverns that have not opened yet are flagged coming_soon. The records also
# carry an "active" field, which is false on every one of them and reflects the
# map widget's selection rather than whether the tavern is open.
#
# No opening hours are published on this page.
#
# No brand:wikidata is set because the chain has no Wikidata item.


class WorldOfBeerUSSpider(Spider):
    name = "world_of_beer_us"
    item_attributes = {"brand": "World of Beer"}
    allowed_domains = ["worldofbeer.com"]
    start_urls = ["https://worldofbeer.com/locations/"]

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Feature]:
        if not (site_info := re.search(r"var site_info\s*=\s*", response.text)):
            self.logger.error("No site_info on the locations page")
            return

        info, _ = json.JSONDecoder().raw_decode(response.text[site_info.end() :])

        for location in json.loads(info.get("locations") or "[]"):
            if location.get("coming_soon"):
                continue

            item = Feature()
            item["ref"] = location["id"]
            item["branch"] = location.get("title")
            item["street_address"] = location.get("address")
            item["city"] = location.get("city")
            item["state"] = location.get("state")
            item["postcode"] = location.get("zip")
            item["phone"] = location.get("phone")
            item["website"] = location.get("permalink")

            # "38.98678959;-76.548033661"
            if len(coordinates := (location.get("latitude_longitude") or "").split(";")) == 2:
                item["lat"], item["lon"] = coordinates

            apply_category(Categories.BAR, item)
            item["extras"]["cuisine"] = "american"

            yield item
