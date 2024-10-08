from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class SaturnDESpider(SitemapSpider, StructuredDataSpider):
    name = "saturn_de"
    item_attributes = {"brand": "Saturn", "brand_wikidata": "Q2543504"}
    allowed_domains = ["www.saturn.de"]
    sitemap_urls = ["https://www.saturn.de/sitemaps/sitemap-marketpages.xml"]
    sitemap_rules = [(r"/de/store/.+", "parse_sd")]
    wanted_types = ["Store"]
