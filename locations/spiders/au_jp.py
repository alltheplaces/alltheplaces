from typing import Any, Iterable

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature

# UQ mobile is a separate KDDI-owned brand that shares this store locator
# (storeClassification "9"); exclude it so only "au" branded shops remain.
UQ_MOBILE_CLASSIFICATION = "9"


class AuJPSpider(Spider):
    name = "au_jp"
    item_attributes = {"brand": "au", "brand_wikidata": "Q307110"}
    allowed_domains = ["www.au.com"]
    start_urls = [
        "https://www.au.com/bin/wcm/au-com/storelocator.json"
        "?northWestLat=46&northWestLng=120&northEastLat=46&northEastLng=156"
        "&southWestLat=20&southWestLng=120&southEastLat=20&southEastLng=156&locale=ja"
    ]

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Feature]:
        for shop in response.json():
            if shop.get("storeClassification") == UQ_MOBILE_CLASSIFICATION:
                continue

            item = Feature()
            item["ref"] = shop["shopNo"]
            item["name"] = shop.get("storeNameDisp") or shop.get("storeName")
            item["lat"] = shop.get("latitude")
            item["lon"] = shop.get("longitude")
            item["state"] = shop.get("address1")
            item["city"] = shop.get("address2")
            item["street_address"] = shop.get("address3")
            item["postcode"] = shop.get("zipCode")
            item["phone"] = shop.get("phoneNo") or shop.get("freeCall") or None
            item["website"] = f"https://www.au.com/storelocator/detail/?shopId={shop['shopNo']}"
            item["country"] = "JP"

            apply_category(Categories.SHOP_MOBILE_PHONE, item)

            yield item
