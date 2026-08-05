from typing import Any, Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class VodacomTZSpider(JSONBlobSpider):
    name = "vodacom_tz"
    item_attributes = {"brand": "Vodacom Tanzania", "brand_wikidata": "Q7939274"}
    locations_key = "data"
    start_urls = ["https://myvodacom.vodacom.co.tz/app/digital-service-engine/api/v1/web/vodacom-shop-form/stores"]

    def post_process_item(self, item: Feature, response: Response, location: dict, **kwargs: Any) -> Iterable[Feature]:
        item["branch"] = item.pop("name").replace("Vodashop ", "")
        item["addr_full"] = location["location"]
        if not (-90 <= float(item["lat"]) <= 90 and -180 <= float(item["lon"]) <= 180):
            item["lat"] = item["lon"] = None
        apply_category(Categories.SHOP_MOBILE_PHONE, item)
        yield item
