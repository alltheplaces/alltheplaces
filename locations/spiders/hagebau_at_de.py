import re

from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider


class HagebauATDESpider(SitemapSpider, StructuredDataSpider):
    name = "hagebau_at_de"
    item_attributes = {"brand": "Hagebaumarkt", "brand_wikidata": "Q1568279"}
    sitemap_urls = [
        "https://www.hagebau.at/sitemap.xml",
        "https://www.hagebau.de/sitemap.xml",
    ]
    sitemap_follow = ["/store/"]
    sitemap_rules = [("", "parse_sd")]

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["lat"], item["lon"] = re.search(r"lat&quot;:(\d+.\d+),&quot;lon&quot;:(\d+.\d+)}", response.text).groups()
        apply_category(Categories.SHOP_DOITYOURSELF, item)
        yield item
