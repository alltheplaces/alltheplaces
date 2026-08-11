import re
from typing import Any, Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class SolidcoreUSSpider(JSONBlobSpider):
    name = "solidcore_us"
    item_attributes = {"brand": "[solidcore]", "brand_wikidata": "Q124429271"}
    start_urls = ["https://prod.api.bluespringhq.com/locations?siteId=5737724"]
    locations_key = "Locations"

    def post_process_item(self, item: Feature, response: Response, feature: dict, **kwargs: Any) -> Iterable[Feature]:
        if feature.get("Address") in (None, "Coming soon"):
            return
        item["ref"] = f"{feature['SiteID']}-{feature['Id']}"
        item["branch"] = re.sub(r"^[A-Z]{2}, ", "", item.pop("name"))
        item["street_address"] = item.pop("addr_full", None)
        item["state"] = feature.get("StateProvCode")
        apply_category(Categories.GYM, item)
        yield item
