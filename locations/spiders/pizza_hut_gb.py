from scrapy.spiders import SitemapSpider

from locations.spiders.vapestore_gb import clean_address
from locations.structured_data_spider import StructuredDataSpider


class PizzaHutGB(SitemapSpider, StructuredDataSpider):
    name = "pizza_hut_gb"
    item_attributes = {"brand": "Pizza Hut", "brand_wikidata": "Q191615"}
    sitemap_urls = ["https://www.pizzahut.co.uk/sitemap.xml"]
    sitemap_rules = [
        (r"https:\/\/www\.pizzahut\.co\.uk\/huts\/[-\w]+\/([-.\w]+)\/$", "parse_sd")
    ]
    wanted_types = ["FastFoodRestaurant"]

    def inspect_item(self, item, response):
        item["street_address"] = clean_address(item["street_address"])

        if item["website"].startswith("https://www.pizzahut.co.uk/huts/"):
            item["brand"] = "Pizza Hut Delivery"
            item["brand_wikidata"] = "Q107293079"

        yield item
