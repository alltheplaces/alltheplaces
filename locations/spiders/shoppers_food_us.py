import json
from typing import Iterable

from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class ShoppersFoodUSSpider(SitemapSpider, JSONBlobSpider):
    name = "shoppers_food_us"
    item_attributes = {"brand": "Shoppers", "brand_wikidata": "Q7501183"}
    allowed_domains = ["shoppersfood.com"]
    sitemap_urls = ["https://www.shoppersfood.com/sitemap.xml"]
    sitemap_rules = [(r"/stores/\d+$", "parse")]

    def extract_json(self, response: TextResponse) -> list[dict]:
        remix_context = json.loads(
            response.xpath('//script[contains(text(), "window.__remixContext")]/text()')
            .get()
            .split("window.__remixContext =", 1)[1]
            .rsplit(";", 1)[0]
        )
        return [remix_context["state"]["loaderData"]["routes/stores.$storeId._index"]["storeDetailsV2"]]

    def pre_process_data(self, feature: dict) -> None:
        feature.update(feature.pop("location"))
        feature["phone"] = feature["phoneNumbers"][0]["value"]

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name")
        item["website"] = response.url
        item["opening_hours"] = OpeningHours()
        for rule in feature["hours"]["weekly"]:
            item["opening_hours"].add_range(
                rule["day"], rule["daily"]["open"]["open"], rule["daily"]["open"]["close"], "%H:%M:%S"
            )
        apply_category(Categories.SHOP_SUPERMARKET, item)
        yield item
