from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature, set_closed
from locations.structured_data_spider import StructuredDataSpider


class PizzaHutUSSpider(SitemapSpider, StructuredDataSpider):
    name = "pizza_hut_us"
    item_attributes = {"brand": "Pizza Hut", "brand_wikidata": "Q191615"}
    PIZZA_HUT = {"brand": "Pizza Hut", "brand_wikidata": "Q191615", "extras": Categories.RESTAURANT.value}
    sitemap_urls = ["https://locations.pizzahut.com/robots.txt"]
    sitemap_rules = [
        (
            r"^https://locations\.pizzahut\.com/\w\w/[^/]+/(?!pizzeria|food-places|takeout|pizza-deals|pizza-delivery|wings)[^/]+$",
            "parse_sd",
        )
    ]
    wanted_types = ["FastFoodRestaurant"]

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        item["image"] = None
        label = response.xpath('//h1[@class="H1"]/text()').get()
        if not label:
            set_closed(item)
        if label == "Pizza Hut Express":
            item["name"] = "Pizza Hut Express"
            apply_category(Categories.FAST_FOOD, item)
        else:
            apply_category(Categories.RESTAURANT, item)

        yield item
