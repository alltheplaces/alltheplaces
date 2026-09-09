import json
from typing import Any, Iterable

from scrapy import Request
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider


class EriksBikeShopUSSpider(StructuredDataSpider):
    name = "eriks_bike_shop_us"
    item_attributes = {"brand": "ERIK'S Bike Board & Ski", "name": "ERIK'S Bike Board & Ski"}
    allowed_domains = ["www.eriksbikeshop.com"]
    start_urls = ["https://www.eriksbikeshop.com/pages/our-stores"]
    wanted_types = ["BikeStore"]
    time_format = "%I:%M%p"
    # Site-wide contact details picked up by StructuredDataSpider's generic
    # email/social discovery, not specific to any one branch.
    drop_attributes = {"email", "facebook"}

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Request]:
        # The store list/map is rendered client side from a GeoJSON blob
        # embedded in the page rather than from real <a> links, so the
        # per-store detail page URLs must be pulled out of this JSON.
        blob = response.css("store-locator script[type='application/json']::text").get()
        data = json.loads(blob)
        for feature in data["locations"]["features"]:
            properties = feature["properties"]
            yield response.follow(
                properties["detailsUrl"],
                callback=self.parse_sd,
                meta={"branch": properties.get("name")},
            )

    def post_process_item(self, item, response: Response, ld_data: dict, **kwargs: Any) -> Iterable[Any]:
        # The JSON-LD "name" is a generic SEO string (e.g. "Bike, Ski and
        # Snowboard Shop in Bayshore, WI"), not a real location name.
        item["name"] = None
        item["branch"] = response.meta.get("branch")
        apply_category(Categories.SHOP_BICYCLE, item)
        yield item
