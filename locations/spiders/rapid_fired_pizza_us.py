import json
import re
from typing import Any, Iterable

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature

# The locations page passes every restaurant to the map's updateMarkers()
# call, with the address, coordinates and the restaurant's page path.
#
# The per restaurant pages those paths point at return branded 404s, so no
# phone or hours are available.
#
# No brand:wikidata is set because the chain has no Wikidata item.


class RapidFiredPizzaUSSpider(Spider):
    name = "rapid_fired_pizza_us"
    item_attributes = {"brand": "Rapid Fired Pizza"}
    allowed_domains = ["rapidfiredpizza.com"]
    start_urls = ["https://rapidfiredpizza.com/locations/"]

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Feature]:
        if not (markers := re.search(r"updateMarkers\(\s*(\{)", response.text)):
            self.logger.error("No markers on the locations page")
            return

        data, _ = json.JSONDecoder().raw_decode(response.text[markers.start(1) :])

        for marker in data.get("marker") or []:
            location = marker.get("@attributes") or {}

            item = Feature()
            item["ref"] = location["id"]
            item["branch"] = location.get("name")
            item["street_address"] = location.get("address")
            item["city"] = location.get("city")
            item["state"] = location.get("state")
            item["postcode"] = location.get("zip")
            item["lat"] = location.get("lat")
            item["lon"] = location.get("lng")

            apply_category(Categories.FAST_FOOD, item)
            item["extras"]["cuisine"] = "pizza"

            yield item
