from typing import Iterable

from chompjs import parse_js_object
from scrapy.http import Response

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class PizzaHutFISpider(JSONBlobSpider):
    name = "pizza_hut_fi"
    item_attributes = {"brand": "Pizza Hut", "brand_wikidata": "Q191615"}
    start_urls = ["https://www.pizzahut.fi/fi/store-locator"]

    def extract_json(self, response):
        data = response.xpath('.//script[@id="__NEXT_DATA__"]/text()').get()
        return parse_js_object(data)["props"]["pageProps"]["data"]["chainStores"]["msg"]

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["name"] = feature["title"]["fi_FI"]
        item["extras"]["name:en"] = feature["title"]["en_US"]
        item["extras"]["name:fi"] = feature["title"]["fi_FI"]
        item["country"] = feature["address"]["countryCode"]
        item["addr_full"] = feature["address"]["formatted"]
        item["city"] = feature["address"]["city"]
        item["lat"] = feature["address"]["latLng"]["lat"]
        item["lon"] = feature["address"]["latLng"]["lng"]
        item["phone"] = feature["contact"]["phone"]
        item["email"] = feature["contact"]["email"]
        apply_category(Categories.RESTAURANT, item)
        apply_yes_no(Extras.DELIVERY, item, feature.get("deliveryAllowed"))
        apply_yes_no(Extras.TAKEAWAY, item, feature.get("pickUpAllwed"))
        yield item
