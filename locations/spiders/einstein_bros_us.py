from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class EinsteinBrosUSSpider(SitemapSpider, StructuredDataSpider):
    name = "einstein_bros_us"
    item_attributes = {"brand": "Einstein Bros. Bagels", "brand_wikidata": "Q5349788"}
    allowed_domains = ["einsteinbros.com"]
    sitemap_urls = ["https://locations.einsteinbros.com/sitemap.xml"]
    sitemap_rules = [(r"/us/[a-z]{2}/[-\w]+/[-\w]+$", "parse_sd")]
