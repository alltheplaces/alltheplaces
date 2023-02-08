from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class PrimantiBrosUSSpider(SitemapSpider, StructuredDataSpider):
    name = "primanti_bros_us"
    item_attributes = {"brand": "Primanti Bros", "brand_wikidata": "Q7243049"}
    sitemap_urls = ["https://locations.primantibros.com/robots.txt"]
    sitemap_rules = [(r"/\d+/$", "parse_sd")]
    json_parser = "json5"
