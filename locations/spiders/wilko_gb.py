from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class WilkoGBSpider(SitemapSpider, StructuredDataSpider):
    name = "wilko_gb"
    item_attributes = {"brand": "Wilko", "brand_wikidata": "Q8002536"}
    allowed_domains = ["stores.wilko.com"]
    sitemap_urls = ["https://stores.wilko.com/sitemap.xml"]
    sitemap_rules = [
        (
            r"https:\/\/stores\.wilko\.com\/gb\/([\w-]+\/[-\w\/]+)$",
            "parse_sd",
        ),
    ]
    wanted_types = ["DepartmentStore"]
