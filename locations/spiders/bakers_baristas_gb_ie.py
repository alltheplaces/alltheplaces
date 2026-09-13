from typing import Iterable

from scrapy.http import Response

from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class BakersBaristasGBIESpider(JSONBlobSpider):
    name = "bakers_baristas_gb_ie"
    item_attributes = {
        "brand_wikidata": "Q85199581",
        "brand": "Bakers + Baristas",
    }
    # allowed_domains = [
    #     "www.bakersbaristas.com",
    # ]
    start_urls = ["https://matthews42.sg-host.com/test-location-app/store-locations.php"]

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name").replace("Bakers + Baristas - ", "")
        yield item
