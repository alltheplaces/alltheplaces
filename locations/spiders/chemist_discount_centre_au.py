from typing import Any

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.pipelines.address_clean_up import clean_address


class ChemistDiscountCentreAUSpider(JSONBlobSpider):
    name = "chemist_discount_centre_au"
    item_attributes = {"brand": "Chemist Discount Centre", "brand_wikidata": "Q141233470"}
    allowed_domains = ["www.chemistdiscountcentre.com.au"]
    start_urls = ["https://www.chemistdiscountcentre.com.au/breeze/frontend/Shops"]

    def extract_json(self, response: Response) -> list[dict]:
        return [
            shop
            for shop in response.json()
            if isinstance(shop, dict) and shop.get("Visible") and shop.get("Name") != "Chemist Discount Centre Online"
        ]

    def post_process_item(self, item: Feature, response: Response, feature: dict, **kwargs: Any) -> Any:
        item["branch"] = item.pop("name").removeprefix("Chemist Discount Centre ")
        item["street_address"] = clean_address([feature.get("StreerNumber"), feature.get("Address")])
        item["addr_full"] = clean_address([item["street_address"], item.pop("city", None), item.get("postcode")])
        item["phone"] = feature.get("ContactNumber1")
        apply_category(Categories.PHARMACY, item)
        yield item
