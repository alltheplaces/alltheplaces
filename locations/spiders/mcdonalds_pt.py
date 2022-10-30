from scrapy.spiders import SitemapSpider
from locations.structured_data_spider import StructuredDataSpider
from locations.spiders.mcdonalds import McDonaldsSpider


class McDonaldsPTSpider(SitemapSpider, StructuredDataSpider):
    name = "mcdonalds_pt"
    item_attributes = McDonaldsSpider.item_attributes
    allowed_domains = ["www.mcdonalds.pt"]
    sitemap_urls = ["https://www.mcdonalds.pt/sitemap"]
    sitemap_rules = [("/restaurantes/", "parse_sd")]
