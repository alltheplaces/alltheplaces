import re
from typing import Any

import scrapy
from scrapy.http import Response

from locations.categories import Access, Categories, Fuel, apply_category, apply_yes_no
from locations.items import Feature


class RoadRangerUSSpider(scrapy.Spider):
    name = "road_ranger_us"
    item_attributes = {"brand": "Road Ranger", "brand_wikidata": "Q7339377"}
    allowed_domains = ["roadrangerusa.com"]

    start_urls = ("https://www.roadrangerusa.com/locations-amenities/find-a-road-ranger",)

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.css(".store-location-row"):
            item = Feature()
            if m := re.search(r"Coordinates:\s+(-?\d+\.\d+), (-?\d+\.\d+)", location.get()):
                item["lat"], item["lon"] = m.groups()

            item["addr_full"] = item["ref"] = (
                location.css(".store-location-teaser__address::text").extract_first().strip()
            )

            amenities = location.css(".store-location-teaser__amenities").get()

            apply_category(Categories.FUEL_STATION, item)
            apply_yes_no(Access.HGV, item, True)
            apply_yes_no(Fuel.DIESEL, item, True)
            apply_yes_no(Fuel.HGV_DIESEL, item, True)
            apply_yes_no(Fuel.PROPANE, item, "Propane" in amenities)
            yield item
