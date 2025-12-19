from typing import Iterable
from urllib.parse import urljoin

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class GoodNeighborPharmacySpider(JSONBlobSpider):
    name = "good_neighbor_pharmacy"
    item_attributes = {"brand": "Good Neighbor Pharmacy", "brand_wikidata": "Q5582813"}
    start_urls = ["https://www.mygnp.com/pharmacies/api/locations/rectangle?neLat=90&neLon=180&swLat=-90&swLon=-180"]

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["branch"] = feature.get("title")
        item["website"] = urljoin("https://www.mygnp.com/pharmacies/", item.pop("name"))
        apply_category(Categories.PHARMACY, item)
        yield item
