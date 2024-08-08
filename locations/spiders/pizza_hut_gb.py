from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider


class PizzaHutGBSpider(SitemapSpider, StructuredDataSpider):
    name = "pizza_hut_gb"
    item_attributes = {"brand": "Pizza Hut", "brand_wikidata": "Q191615"}
    PIZZA_HUT_DELIVERY = {"brand": "Pizza Hut Delivery", "brand_wikidata": "Q107293079"}
    sitemap_urls = ["https://www.pizzahut.co.uk/sitemap.xml"]
    sitemap_rules = [(r"https:\/\/www\.pizzahut\.co\.uk\/huts\/[-\w]+\/([-.\w]+)\/$", "parse_sd")]

    def post_process_item(self, item, response, ld_data, **kwargs):
        if item["website"].startswith("https://www.pizzahut.co.uk/huts/"):
            item.update(self.PIZZA_HUT_DELIVERY)
            apply_category(Categories.FAST_FOOD, item)
        else:
            apply_category(Categories.RESTAURANT, item)

        if not item["opening_hours"]:
            return

        yield item
