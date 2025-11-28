from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class MillerAndCarterGBSpider(SitemapSpider, StructuredDataSpider):
    name = "miller_and_carter_gb"
    item_attributes = {"brand": "Miller & Carter", "brand_wikidata": "Q87067401"}
    sitemap_urls = ["https://www.millerandcarter.co.uk/sitemap.xml"]
    sitemap_rules = [(r"/restaurants/[^/]+/[^/]+$", "parse_sd")]
    requires_proxy = True
