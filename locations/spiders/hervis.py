from typing import Iterable

from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class HervisSpider(JSONBlobSpider):
    name = "hervis"
    item_attributes = {"brand": "Hervis", "brand_wikidata": "Q1614816"}
    start_urls = ["https://cdn.shopify.com/s/files/1/0997/4828/2752/files/Storeinfos.json"]

    def extract_json(self, response: TextResponse) -> list[dict]:
        shops = []
        for region in response.json().get("hotspots", {}).get("land", {}).get("bundesland", []):
            shops.extend(region.get("shop", []))
        return shops

    def post_process_item(self, item: Feature, response: TextResponse, location: dict) -> Iterable[Feature]:
        raw_name = item.pop("name", "")
        item["branch"] = raw_name.split(" ", 2)[-1] if raw_name else None
        item["street_address"] = location.get("adresse")
        item["city"] = location.get("ort")
        item["postcode"] = str(location.get("plz")) if location.get("plz") else None
        item["country"] = location.get("landcode")
        item["phone"] = location.get("telefon")
        item["lat"] = location.get("gps_x")
        item["lon"] = location.get("gps_y")
        apply_category(Categories.SHOP_SPORTS, item)

        yield item
