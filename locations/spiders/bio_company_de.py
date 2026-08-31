from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.uberall import UberallSpider


class BioCompanyDESpider(UberallSpider):
    name = "bio_company_de"
    item_attributes = {"brand": "Bio Company", "brand_wikidata": "Q864179"}
    key = "4w3OLJTTT66unD30WlbJhuit7Hd45w"

    def post_process_item(self, item: Feature, response: Response, location: dict) -> Iterable[Feature]:
        apply_category(Categories.SHOP_SUPERMARKET, item)
        item["branch"] = item.pop("name").removeprefix("BIO COMPANY ")
        item["name"] = "Bio Company"
        yield item
