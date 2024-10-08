from scrapy.spiders import SitemapSpider

from locations.spiders.mcdonalds import McdonaldsSpider
from locations.structured_data_spider import StructuredDataSpider


class McdonaldsPTSpider(SitemapSpider, StructuredDataSpider):
    name = "mcdonalds_pt"
    item_attributes = McdonaldsSpider.item_attributes
    allowed_domains = ["www.mcdonalds.pt"]
    sitemap_urls = ["https://www.mcdonalds.pt/sitemap"]
    sitemap_rules = [("/restaurantes/", "parse_sd")]
