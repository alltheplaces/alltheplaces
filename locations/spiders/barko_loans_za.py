from typing import Any, Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class BarkoLoansZASpider(JSONBlobSpider):
    name = "barko_loans_za"
    item_attributes = {
        "brand": "Barko Loans",
        "brand_wikidata": "Q118185897",
    }
    start_urls = ["https://www.barko.co.za/Home/GetAllBranches"]
    no_refs = True

    def post_process_item(self, item: Feature, response: Response, feature: dict, **kwargs: Any) -> Iterable[Feature]:
        item["branch"] = item.pop("name")
        item["street_address"] = feature["branchOfficeAddress"]
        item["city"] = feature["branchTown"]
        item["state"] = feature["branchProvince"]
        item["phone"] = feature.get("branchOfficeNumber")
        item["email"] = feature.get("branchEmail")
        item["lat"] = feature.get("branchLatitude")
        item["lon"] = feature.get("branchLongitude")

        apply_category(Categories.SHOP_MONEY_LENDER, item)

        yield item
