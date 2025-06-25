from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class TCBYSpider(JSONBlobSpider):
    name = "tcby"
    item_attributes = {"brand": "TCBY", "brand_wikidata": "Q7669631"}
    start_urls = [
        "https://www.tcby.com/wp-json/wpgmza/v1/features/base64eJyrVkrLzClJLVKyUqqOUcpNLIjPTIlRsopRMjSPUdIBiRRnlBZ4uhQDBaNjgQLJpcUl+blumak5KRCxWqVaABb2FvE"
    ]
    locations_key = "markers"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name")
        apply_category(Categories.ICE_CREAM, item)
        yield item
