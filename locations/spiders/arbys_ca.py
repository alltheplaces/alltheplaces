from scrapy.spiders import SitemapSpider

from locations.spiders.arbys_us import ArbysUSSpider
from locations.structured_data_spider import StructuredDataSpider


class ArbysCASpider(SitemapSpider, StructuredDataSpider):
    name = "arbys_ca"
    item_attributes = ArbysUSSpider.item_attributes
    sitemap_urls = ["https://locations.arbys.ca/sitemap.xml"]
    sitemap_rules = [(r"ca/\w\w/[^/]+/[^/]+.html", "parse")]
    wanted_types = ["Restaurant"]
