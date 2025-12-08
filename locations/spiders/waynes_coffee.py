from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class WaynesCoffeeSpider(SitemapSpider, StructuredDataSpider):
    name = "waynes_coffee"
    item_attributes = {"brand": "Wayne's Coffee", "brand_wikidata": "Q2637272"}
    sitemap_urls = ["https://www.waynescoffee.se/sitemap.xml"]
    sitemap_rules = [(r"/kafe/[\w-]+/", "parse_sd")]
    wanted_types = ["CafeOrCoffeeShop"]

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        item["ref"] = response.url
        item["branch"] = item.pop("name").removeprefix("Wayne's Coffee ")

        yield item
