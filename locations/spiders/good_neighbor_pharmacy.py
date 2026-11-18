from typing import Any, Iterable
from urllib.parse import urljoin

from scrapy.http import Request, Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.linked_data_parser import LinkedDataParser


class GoodNeighborPharmacySpider(JSONBlobSpider):
    name = "good_neighbor_pharmacy"
    item_attributes = {"brand": "Good Neighbor Pharmacy", "brand_wikidata": "Q5582813"}
    start_urls = ["https://www.mygnp.com/pharmacies/api/locations/rectangle?neLat=90&neLon=180&swLat=-90&swLon=-180"]

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["branch"] = feature.get("title")
        item["website"] = urljoin("https://www.mygnp.com/pharmacies/", item.pop("name") + "/")
        apply_category(Categories.PHARMACY, item)
        yield Request(item["website"], callback=self.parse_details, cb_kwargs={"item": item})

    def parse_details(self, response: Response, item: Feature, **kwargs: Any) -> Any:
        if ld := LinkedDataParser.find_linked_data(response, "Pharmacy"):
            item["phone"] = ld.get("telephone")
            if address := ld.get("address"):
                item["street_address"] = address.get("streetAddress")
                item["postcode"] = address.get("postalCode")
            oh = LinkedDataParser.parse_opening_hours(ld)
            if oh.day_hours:
                item["opening_hours"] = oh
        yield item
