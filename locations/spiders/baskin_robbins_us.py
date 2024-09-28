import re

from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class BaskinRobbinsUSSpider(SitemapSpider, StructuredDataSpider):
    name = "baskin_robbins_us"
    item_attributes = {"brand": "Baskin-Robbins", "brand_wikidata": "Q584601"}
    sitemap_urls = ["https://locations.baskinrobbins.com/robots.txt"]
    sitemap_rules = [(r"/\w\w/[-\w]+/[-\w]+", "parse")]
    wanted_types = ["IceCreamShop"]
    drop_attributes = {"image"}

    def post_process_item(self, item, response, ld_data, **kwargs):
        if item.get("name") == "Baskin-Robbins - Closed™":
            return

        item["ref"] = item["website"] = response.url
        if m := re.search(r'"geocodedCoordinate":{"latitude":(-?\d+\.\d+),"longitude":(-?\d+\.\d+)}', response.text):
            item["lat"], item["lon"] = m.groups()

        yield item
