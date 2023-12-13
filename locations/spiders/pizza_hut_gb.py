from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.spiders.vapestore_gb import clean_address
from locations.structured_data_spider import StructuredDataSpider


class PizzaHutGB(SitemapSpider, StructuredDataSpider):
    name = "pizza_hut_gb"
    item_attributes = {"brand": "Pizza Hut", "brand_wikidata": "Q191615"}
    PIZZA_HUT_DELIVERY = {"brand": "Pizza Hut Delivery", "brand_wikidata": "Q107293079"}
    sitemap_urls = ["https://www.pizzahut.co.uk/sitemap.xml"]
    sitemap_rules = [(r"https:\/\/www\.pizzahut\.co\.uk\/huts\/[-\w]+\/([-.\w]+)\/$", "parse_sd")]

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["street_address"] = clean_address(item["street_address"])

        if item["website"].startswith("https://www.pizzahut.co.uk/huts/"):
            item.update(self.PIZZA_HUT_DELIVERY)
            apply_category(Categories.FAST_FOOD, item)
        else:
            apply_category(Categories.RESTAURANT, item)

        if not item["opening_hours"]:
            return

        yield item
