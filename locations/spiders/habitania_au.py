from typing import Iterable

from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class HabitaniaAUSpider(JSONBlobSpider):
    name = "habitania_au"
    item_attributes = {"brand": "Habitania", "brand_wikidata": "Q117923291"}
    start_urls = ["https://storelocator.metizapps.com/v2/api/front/store-locator/?shop=hab2015.myshopify.com"]
    locations_key = "stores"

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name").replace("Habitania ", "")
        item["name"] = self.item_attributes["brand"]
        apply_category(Categories.SHOP_HOUSEWARE, item)
        yield item
