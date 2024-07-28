from scrapy.spiders import SitemapSpider

from locations.spiders.five_guys_us import FiveGuysUSSpider
from locations.structured_data_spider import StructuredDataSpider


class FiveGuysCNSpider(SitemapSpider, StructuredDataSpider):
    name = "five_guys_cn"
    item_attributes = FiveGuysUSSpider.item_attributes
    sitemap_urls = ["https://restaurants.fiveguys.cn/sitemap.xml"]
    sitemap_rules = [(r"^https://restaurants\.fiveguys\.cn\/en_cn\/[^/]+$", "parse_sd")]
