from typing import Iterable

from scrapy.http import Request, Response

from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.pipelines.address_clean_up import merge_address_lines


class BritishGardenCentresGBSpider(JSONBlobSpider):
    name = "british_garden_centres_gb"
    item_attributes = {"brand": "British Garden Centres", "brand_wikidata": "Q114243480"}
    start_urls = [
        "https://www.britishgardencentres.com/wp-admin/admin-ajax.php?action=store_search&lat=53.58424&lng=-0.48261&max_results=100&search_radius=25&autoload=1"
    ]

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Request]:
        if not item["website"].startswith("http"):
            item["name"] = feature["store"]
            item["website"] = "https://www.britishgardencentres.com" + item["website"]
            item["street_address"] = item.pop("addr_full")
        yield item
