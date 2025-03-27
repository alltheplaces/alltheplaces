from typing import Iterable

from scrapy.http import Response

from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class FireawayGBSpider(JSONBlobSpider):
    name = "fireaway_gb"
    allowed_domains = ["fireaway.co.uk"]
    item_attributes = {"brand_wikidata": "Q110484131"}
    start_urls = ["https://api.fireaway.co.uk/localization-api/api/v2/stores/pickup/"]

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name").removeprefix("Fireaway ")
        item["website"] = None
        yield item
