import re

from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class FamousFootwearSpider(SitemapSpider, StructuredDataSpider):
    name = "famous_footwear"
    item_attributes = {"brand": "Famous Footwear", "brand_wikidata": "Q5433457"}
    sitemap_urls = ["https://ecomprdsharedstorage.blob.core.windows.net/sitemaps/20000/stores-sitemap.xml"]
    sitemap_rules = [("", "parse_sd")]
    wanted_types = ["Store"]
    requires_proxy = "US"

    def inspect_item(self, item, response):
        matches = re.search(r'location: \["(.*)", "(.*)"\],', response.text)
        item["lat"], item["lon"] = matches[1], matches[2]
        yield item
