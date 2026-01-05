from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class DieselSpider(JSONBlobSpider):
    name = "diesel"
    item_attributes = {"brand": "Diesel", "brand_wikidata": "Q158285"}
    start_urls = [
        "https://uk.diesel.com/on/demandware.store/Sites-DieselCA-Site/en_CA/StoreFinder-SearchByBoundaries?latmin=-90&latmax=90&lngmin=-180&lngmax=180"
    ]
    locations_key = ["stores", "stores"]

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        if email := item.get("email"):
            item["email"] = email.replace(" ", "")

        item["website"] = item["ref"] = "https://uk.diesel.com/en/store-detail?sid={}".format(feature["ID"])

        if item["name"].startswith("DIESEL ACCESSORIES STORE "):
            item["branch"] = item.pop("name").removeprefix("DIESEL ACCESSORIES STORE ")
            item["name"] = "Diesel Accessories"
        elif item["name"].startswith("DIESEL KID OUTLET "):
            item["branch"] = item.pop("name").removeprefix("DIESEL KID OUTLET ")
            item["name"] = "Diesel Kid Outlet"
        elif item["name"].startswith("DIESEL KID STORE "):
            item["branch"] = item.pop("name").removeprefix("DIESEL KID STORE ")
            item["name"] = "Diesel Kid"
        elif item["name"].startswith("DIESEL MENSWEAR STORE "):
            item["branch"] = item.pop("name").removeprefix("DIESEL MENSWEAR STORE ")
            item["name"] = "Diesel Menswear"
        elif item["name"].startswith("DIESEL OUTLET "):
            item["branch"] = item.pop("name").removeprefix("DIESEL OUTLET ")
            item["name"] = "Diesel Outlet"
        elif item["name"].startswith("DIESEL STORE "):
            item["branch"] = item.pop("name").removeprefix("DIESEL STORE ")
            item["name"] = "Diesel"
        elif item["name"].startswith("DIESEL WOMENSWEAR STORE "):
            item["branch"] = item.pop("name").removeprefix("DIESEL WOMENSWEAR STORE ")
            item["name"] = "Diesel Womenswear"
        else:
            item["branch"] = item.pop("name").removeprefix("DIESEL ")

        apply_category(Categories.SHOP_CLOTHES, item)

        yield item
