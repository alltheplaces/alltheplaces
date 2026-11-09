from typing import Any, Iterable

import chompjs
from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class PizzaExpressGBSpider(SitemapSpider, StructuredDataSpider):
    name = "pizza_express_gb"
    item_attributes = {"brand": "PizzaExpress", "brand_wikidata": "Q662845"}
    sitemap_urls = ["https://locations.pizzaexpress.com/sitemap.xml"]
    sitemap_rules = [(r"com/(?!restaurants)[^/]+$", "parse_sd")]
    wanted_types = ["FoodEstablishment"]
    drop_attributes = {"image", "name", "facebook"}

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs: Any) -> Iterable[Feature]:
        item["ref"] = response.url
        item["branch"] = response.xpath("//h1/text()").get()
        if item.get("postcode", "").startswith("JE"):
            item["country"] = "JE"

        for block in response.xpath('//script[@type="application/ld+json"]/text()').getall():
            if geo := chompjs.parse_js_object(block).get("credentialSubject", {}).get("geo"):
                item["lat"] = geo.get("latitude")
                item["lon"] = geo.get("longitude")

        facilities = response.xpath("//span/text()").getall()
        apply_yes_no(Extras.WIFI, item, "WiFi" in facilities)
        apply_yes_no(Extras.OUTDOOR_SEATING, item, "Outdoor Dining" in facilities)
        apply_yes_no(Extras.DELIVERY, item, "Delivery" in facilities)
        apply_yes_no(Extras.TAKEAWAY, item, "Collection" in facilities)

        apply_category(Categories.RESTAURANT, item)

        yield item
