from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature


class PostnetZASpider(Spider):
    name = "postnet_za"
    item_attributes = {"brand": "PostNet", "brand_wikidata": "Q7233611"}
    start_urls = ["https://www.postnet.co.za/cart_store-json_list/"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json():
            item = Feature()
            item["ref"] = location["code"]
            item["lat"] = location["latitude"]
            item["lon"] = location["longitude"]
            item["branch"] = location["store_name"]
            item["street_address"] = location["physical_address"]
            item["city"] = location["town"]
            item["postcode"] = location["postal_code"]
            item["phone"] = location["telephone"]
            item["email"] = location["email"]
            item["website"] = "https://www.postnet.co.za/stores/{}/{}".format(location["tag_name"], location["code"])

            apply_category(Categories.POST_OFFICE, item)

            yield item
