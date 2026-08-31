from typing import Any

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.pipelines.address_clean_up import clean_address

AU_STATES = {
    "ACT": "ACT",
    "NSW": "NSW",
    "NT": "NT",
    "QLD": "QLD",
    "QUEENSLAND": "QLD",
    "SA": "SA",
    "TAS": "TAS",
    "TASMANIA": "TAS",
    "VIC": "VIC",
    "VICTORIA": "VIC",
    "WA": "WA",
}


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

    def pre_process_data(self, feature: dict) -> None:
        feature["ref"] = str(feature.pop("Id"))
        feature["street_address"] = clean_address([feature.pop("StreerNumber", None), feature.pop("Address", None)])
        feature["phone"] = feature.pop("ContactNumber1", None)

        # "Suburb" is usually "<suburb> <state>", but is sometimes just the
        # suburb or, for a few records, only the state.
        parts = (feature.pop("Suburb", None) or "").split()
        if parts and parts[-1].upper() in AU_STATES:
            feature["state"] = AU_STATES[parts.pop().upper()]
        feature["city"] = " ".join(parts)

    def post_process_item(self, item: Feature, response: Response, feature: dict, **kwargs: Any) -> Any:
        item["branch"] = item.pop("name").removeprefix("Chemist Discount Centre ")
        apply_category(Categories.PHARMACY, item)
        yield item
