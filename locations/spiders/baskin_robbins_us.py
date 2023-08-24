from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class BaskinRobbinsUSSpider(SitemapSpider, StructuredDataSpider):
    name = "baskin_robbins_us"
    item_attributes = {"brand": "Baskin-Robbins", "brand_wikidata": "Q584601"}
    sitemap_urls = ["https://locations.baskinrobbins.com/robots.txt"]
    sitemap_rules = [(r"/\w\w/[-\w]+/[-\w]+", "parse")]
    wanted_types = ["IceCreamShop"]

    def post_process_item(self, item, response, ld_data, **kwargs):
        if not item.get("name") == "Baskin-Robbins - Closed™":
            yield item
