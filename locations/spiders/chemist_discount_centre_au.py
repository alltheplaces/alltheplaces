from typing import Any, AsyncIterator

from scrapy import FormRequest
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS, OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.pipelines.address_clean_up import clean_address


class ChemistDiscountCentreAUSpider(JSONBlobSpider):
    name = "chemist_discount_centre_au"
    item_attributes = {"brand": "Chemist Discount Centre", "brand_wikidata": "Q141233470"}
    allowed_domains = ["www.chemistdiscountcentre.com.au"]

    async def start(self) -> AsyncIterator[FormRequest]:
        yield FormRequest(
            "https://www.chemistdiscountcentre.com.au/Shops/Nearest",
            formdata={"lat": "-25.363882", "lng": "131.044922"},
        )

    def extract_json(self, response: Response) -> list[dict]:
        return [
            shop
            for shop in response.json()
            if isinstance(shop, dict) and shop.get("Visible") and shop.get("Name") != "Chemist Discount Centre Online"
        ]

    def post_process_item(self, item: Feature, response: Response, feature: dict, **kwargs: Any) -> Any:
        item["branch"] = item.pop("name").removeprefix("Chemist Discount Centre ")
        # "StreerNumber" is the API's own spelling
        item["street_address"] = clean_address([feature.get("StreerNumber"), feature.get("Address")])
        item["addr_full"] = clean_address([item["street_address"], item.pop("city", None), item.get("postcode")])
        item["phone"] = feature.get("ContactNumber1")

        item["opening_hours"] = OpeningHours()
        for rule in feature.get("ShopsHours") or []:
            # Type 0 is the shop itself; other types are delivery and click and collect windows
            if rule["Type"] != 0:
                continue
            day = DAYS[(rule["Weekday"] - 1) % 7]
            if rule["IsAvailable"]:
                item["opening_hours"].add_range(day, rule["Start"], rule["End"], "%H:%M:%S")
            else:
                item["opening_hours"].set_closed(day)

        apply_category(Categories.PHARMACY, item)
        yield item
