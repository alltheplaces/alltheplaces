import re
from typing import Iterable

from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class GlenEiraCityCouncilToiletsAUSpider(JSONBlobSpider):
    name = "glen_eira_city_council_toilets_au"
    item_attributes = {"operator": "Glen Eira City Council", "operator_wikidata": "Q56477767", "state": "VIC"}
    allowed_domains = ["connect.pozi.com"]
    start_urls = ["https://connect.pozi.com/userdata/gleneira-publisher/Council-Facilities-and-Services/Public_Toilet.json"]
    locations_key = "features"
    custom_settings = {
        "ROBOTSTXT_OBEY": False,  # Avoid HTTP 403 error
    }

    def pre_process_data(self, feature: dict) -> None:
        feature.update(feature.pop("properties"))

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        item["ref"] = str(feature["id"])  # Note: cannot use feature_id because some are null
        if addr := re.search(r"(?<=, )(\d+ .+)", feature["feature_location"]):
            item["addr_full"] = addr.group(1)
        apply_category(Categories.TOILETS, item)
        item["extras"]["fee"] = "no"
        if located_in := feature.get("site_name"):
            item["located_in"] = located_in
        yield item
